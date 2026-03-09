"""Analysis orchestration service.

This module performs the application's core analysis computation.

Responsibilities
----------------
- Validate/coerce incoming parameter values into a strongly typed
    :class:`AnalysisInputs` instance.
- Compute derived quantities and ATES KPI results using functions in
    :mod:`geoninja_backend.services.analysis_calcs`.
- Emit results as :class:`~geoninja_backend.models.analysis_run.AnalysisRunResults`
    with stable `key` and `unit` fields.

Contracts
---------
Result keys/units are mirrored in registries:

- :data:`~geoninja_backend.core.analysis_result_registry.DERIVED_QUANTITY_REGISTRY`
- :data:`~geoninja_backend.core.analysis_result_registry.ATES_KPI_RESULT_REGISTRY`

Those registries are validated against the shared contract file
`contracts/analysis_results.json` (see backend tests). If you add/remove/rename a
result or change a unit, update both the registries and the contract.

Error handling
--------------
This service returns an ``AnalysisRunResults`` object in all cases:

- On validation errors, status is ``error`` and `message` contains details.
- On unexpected errors, status is ``error`` with a generic message.
"""

from pydantic import BaseModel, ConfigDict

from geoninja_backend.core.analysis_result_registry import (
    ATES_KPI_RESULT_REGISTRY,
    DERIVED_QUANTITY_REGISTRY,
    AtesKpiResultKey,
    DerivedQuantityKey,
)
from geoninja_backend.models.analysis_run import AnalysisResultItem, AnalysisRunResults
from geoninja_backend.models.common import TimePeriod
from geoninja_backend.services.analysis_calcs import (
    calc_aq_vol_heat_cap,
    calc_darcy_velo,
    calc_hydr_trans,
    calc_mass_flow_rate,
    calc_max_vol_flow_rate,
    calc_pore_velo,
    calc_retard_fact,
    calc_therm_area,
    calc_therm_density,
    calc_therm_front_velo,
    calc_therm_rad,
    calc_therm_rad_adv,
    calc_therm_rad_voleq,
    calc_therm_rate,
    calc_vol_heat_cap,
)
from geoninja_backend.services.param_access import (
    ParamValidationError,
    get_date_from_key_value_dict,
    get_float_from_key_value_dict,
    get_int_from_key_value_dict,
)


def perform_analysis(params: dict[str, float | str]) -> AnalysisRunResults:
    """Run the analysis for a set of input parameters.

    Args:
        params: Parameter mapping (typically from the API request). Keys are the
            canonical parameter identifiers (e.g., ``thickness``, ``hydrCond``).
            Values are expected to already be in SI units.

    Returns:
        An :class:`~geoninja_backend.models.analysis_run.AnalysisRunResults`
        containing:
        - `status`: ``ok`` or ``error``
        - `message`: optional human-readable context
        - `derived_quantities` and `ates_kpi_results`: lists of
          :class:`~geoninja_backend.models.analysis_run.AnalysisResultItem`

    Notes:
        This function deliberately does not raise for expected validation
        problems; those are converted into an ``error`` result.
    """
    try:
        inputs = _build_analysis_inputs(params)
    except ParamValidationError as e:
        return AnalysisRunResults(status="error", message=str(e))
    except Exception:
        return AnalysisRunResults(status="error", message="ATES KPI computation failed")

    fluid_vol_heat_cap = calc_vol_heat_cap(inputs.fluid_density, inputs.fluid_spec_heat_cap)
    rock_vol_heat_cap = calc_vol_heat_cap(inputs.rock_density, inputs.rock_spec_heat_cap)
    aq_vol_heat_cap = calc_aq_vol_heat_cap(fluid_vol_heat_cap, rock_vol_heat_cap, inputs.porosity)
    hydr_trans = calc_hydr_trans(inputs.hydr_cond, inputs.thickness)
    darcy_velo = calc_darcy_velo(inputs.hydr_cond, inputs.hydr_grad)
    pore_velo = calc_pore_velo(darcy_velo, inputs.porosity)
    retard_fact = calc_retard_fact(fluid_vol_heat_cap, aq_vol_heat_cap, inputs.porosity)
    therm_front_velo = calc_therm_front_velo(pore_velo, retard_fact)
    heat_duration_days = inputs.heat_period.duration_days()
    cool_duration_days = inputs.cool_period.duration_days()
    heat_duration_secs = inputs.heat_period.duration_secs()
    cool_duration_secs = inputs.cool_period.duration_secs()
    storativity = 0.1 * inputs.porosity  # shorthand in abscence of storativity
    max_vol_flow_rate_heat = calc_max_vol_flow_rate(
        inputs.well_radius, inputs.well_distance, inputs.max_drawdown, hydr_trans, storativity, heat_duration_secs
    )
    max_vol_flow_rate_cool = calc_max_vol_flow_rate(
        inputs.well_radius, inputs.well_distance, inputs.max_drawdown, hydr_trans, storativity, cool_duration_secs
    )
    max_mass_flow_rate_heat = calc_mass_flow_rate(max_vol_flow_rate_heat, inputs.fluid_density)
    max_mass_flow_rate_cool = calc_mass_flow_rate(max_vol_flow_rate_cool, inputs.fluid_density)
    max_heat_rate = calc_therm_rate(max_mass_flow_rate_heat, inputs.fluid_spec_heat_cap, inputs.temp_diff)
    max_cool_rate = calc_therm_rate(max_mass_flow_rate_cool, inputs.fluid_spec_heat_cap, inputs.temp_diff)
    therm_rad_vol_eq_warm_well = calc_therm_rad_voleq(
        fluid_vol_heat_cap,
        aq_vol_heat_cap,
        max_vol_flow_rate_cool,
        cool_duration_secs,
        inputs.thickness,
    )
    therm_rad_vol_eq_cold_well = calc_therm_rad_voleq(
        fluid_vol_heat_cap,
        aq_vol_heat_cap,
        max_vol_flow_rate_heat,
        heat_duration_secs,
        inputs.thickness,
    )
    therm_rad_adv_warm_well = calc_therm_rad_adv(therm_front_velo, cool_duration_secs)
    therm_rad_adv_cold_well = calc_therm_rad_adv(therm_front_velo, heat_duration_secs)
    therm_rad_warm_well = calc_therm_rad(therm_rad_vol_eq_warm_well, therm_rad_adv_warm_well)
    therm_rad_cold_well = calc_therm_rad(therm_rad_vol_eq_cold_well, therm_rad_adv_cold_well)
    therm_area = calc_therm_area(
        therm_rad_warm_well,
        therm_rad_cold_well,
        inputs.well_distance,
    )
    max_heat_density = calc_therm_density(max_heat_rate, therm_area)
    max_cool_density = calc_therm_density(max_cool_rate, therm_area)

    # Build ATES KPI results
    ates_kpi_results = [
        _ates_kpi_item("maxVolFlowRateHeat", max_vol_flow_rate_heat),
        _ates_kpi_item("maxVolFlowRateCool", max_vol_flow_rate_cool),
        _ates_kpi_item("maxMassFlowRateHeat", max_mass_flow_rate_heat),
        _ates_kpi_item("maxMassFlowRateCool", max_mass_flow_rate_cool),
        _ates_kpi_item("maxHeatRate", max_heat_rate),
        _ates_kpi_item("maxCoolRate", max_cool_rate),
        _ates_kpi_item("thermRadVolEqWarmWell", therm_rad_vol_eq_warm_well),
        _ates_kpi_item("thermRadVolEqColdWell", therm_rad_vol_eq_cold_well),
        _ates_kpi_item("thermRadAdvWarmWell", therm_rad_adv_warm_well),
        _ates_kpi_item("thermRadAdvColdWell", therm_rad_adv_cold_well),
        _ates_kpi_item("thermRadWarmWell", therm_rad_warm_well),
        _ates_kpi_item("thermRadColdWell", therm_rad_cold_well),
        _ates_kpi_item("thermArea", therm_area),
        _ates_kpi_item("maxHeatDensity", max_heat_density),
        _ates_kpi_item("maxCoolDensity", max_cool_density),
    ]

    # Build derived quantities
    derived_quantities = [
        _derived_quantity_item("fluidVolHeatCap", fluid_vol_heat_cap),
        _derived_quantity_item("rockVolHeatCap", rock_vol_heat_cap),
        _derived_quantity_item("aqVolHeatCap", aq_vol_heat_cap),
        _derived_quantity_item("hydrTrans", hydr_trans),
        _derived_quantity_item("darcyVelo", darcy_velo),
        _derived_quantity_item("poreVelo", pore_velo),
        _derived_quantity_item("retardFact", retard_fact),
        _derived_quantity_item("thermFrontVelo", therm_front_velo),
        _derived_quantity_item("storativity", storativity),
        _derived_quantity_item("heatingDuration", heat_duration_days),
        _derived_quantity_item("coolingDuration", cool_duration_days),
    ]

    return AnalysisRunResults(
        ates_kpi_results=ates_kpi_results,
        derived_quantities=derived_quantities,
        status="ok",
        message=None,
    )


class AnalysisInputs(BaseModel):
    """Validated inputs required to run the analysis.

    All values are expected to be in SI units (or dimensionless where
    appropriate) by the time they reach this model.

    Instances are produced by :func:`_build_analysis_inputs`.
    """

    fluid_density: float
    fluid_spec_heat_cap: float
    porosity: float
    hydr_cond: float
    hydr_grad: float
    thickness: float
    well_radius: float
    well_distance: float
    max_drawdown: float
    temp_diff: float
    rock_density: float
    rock_spec_heat_cap: float
    heat_period: TimePeriod
    cool_period: TimePeriod

    model_config = ConfigDict(extra="forbid")


def _build_analysis_inputs(params: dict[str, float | str]) -> AnalysisInputs:
    """Extract and validate analysis inputs from a raw params mapping.

    This converts the API-facing parameter dictionary into strongly typed fields
    used by the computational routines.

    Raises:
        ParamValidationError: If a required key is missing or cannot be coerced
            to the expected type.
        ValueError: If time-period construction fails (e.g., dates in different
            years).
    """
    year = get_int_from_key_value_dict(params, "year")
    thickness = get_float_from_key_value_dict(params, "thickness")
    well_radius = get_float_from_key_value_dict(params, "wellRadius")
    well_distance = get_float_from_key_value_dict(params, "wellDistance")
    max_drawdown = get_float_from_key_value_dict(params, "maxDrawdown")
    fluid_density = get_float_from_key_value_dict(params, "fluidDensity")
    fluid_spec_heat_cap = get_float_from_key_value_dict(params, "fluidSpecHeatCap")
    porosity = get_float_from_key_value_dict(params, "porosity")
    hydr_cond = get_float_from_key_value_dict(params, "hydrCond")
    hydr_grad = get_float_from_key_value_dict(params, "hydrGrad")
    temp_diff = get_float_from_key_value_dict(params, "tempDiff")
    rock_density = get_float_from_key_value_dict(params, "rockDensity")
    rock_spec_heat_cap = get_float_from_key_value_dict(params, "rockSpecHeatCap")
    heat_period_start = get_date_from_key_value_dict(params, "heatPeriodStart", year=year)
    heat_period_end = get_date_from_key_value_dict(params, "heatPeriodEnd", year=year)
    cool_period_start = get_date_from_key_value_dict(params, "coolPeriodStart", year=year)
    cool_period_end = get_date_from_key_value_dict(params, "coolPeriodEnd", year=year)

    # Construct heating and cooling time periods
    heat_period = TimePeriod(start=heat_period_start, end=heat_period_end)
    cool_period = TimePeriod(start=cool_period_start, end=cool_period_end)

    return AnalysisInputs(
        fluid_density=fluid_density,
        fluid_spec_heat_cap=fluid_spec_heat_cap,
        porosity=porosity,
        hydr_cond=hydr_cond,
        hydr_grad=hydr_grad,
        thickness=thickness,
        well_radius=well_radius,
        well_distance=well_distance,
        max_drawdown=max_drawdown,
        temp_diff=temp_diff,
        rock_density=rock_density,
        rock_spec_heat_cap=rock_spec_heat_cap,
        heat_period=heat_period,
        cool_period=cool_period,
    )


def _derived_quantity_item(key: DerivedQuantityKey, value: float | str | None) -> AnalysisResultItem:
    """Build a derived-quantity result item using the registry to supply units."""
    reg = DERIVED_QUANTITY_REGISTRY[key]
    return AnalysisResultItem(key=key, value=value, unit=reg["unit"])


def _ates_kpi_item(key: AtesKpiResultKey, value: float | str | None) -> AnalysisResultItem:
    """Build an ATES KPI result item using the registry to supply units."""
    reg = ATES_KPI_RESULT_REGISTRY[key]
    return AnalysisResultItem(key=key, value=value, unit=reg["unit"])
