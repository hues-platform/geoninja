"""Analysis calculation primitives (pure functions).

This module contains small, unit-aware helper functions used by the analysis
service. Each function implements a single mathematical relationship and is
intended to be easy to test and reuse.

Units and conventions
---------------------
All quantities in this module use SI base units:

- length: meters (m)
- area: square meters (m²)
- time: seconds (s)
- mass: kilograms (kg)
- energy: joules (J)
- power: watts (W)
- temperature difference: kelvin (K)

No unit conversion is performed inside these functions; callers are responsible
for supplying values in the expected units.

Dependencies
------------
The groundwater drawdown-based flow-rate calculation uses the exponential
integral via :func:`scipy.special.expi`.
"""

import math

from scipy.special import expi


def calc_hydr_trans(hydr_cond: float, thickness: float) -> float:
    """
    Calculate hydraulic transmissivity as the product of hydraulic conductivity and thickness.

    Parameters
    ----------
    hydr_cond : float
        Hydraulic conductivity (m/s).
    thickness : float
        Thickness of the aquifer (m).

    Returns
    -------
    float
        Hydraulic transmissivity (m²/s).
    """
    if hydr_cond <= 0:
        raise ValueError("hydr_cond must be positive")
    if thickness <= 0:
        raise ValueError("thickness must be positive")
    return hydr_cond * thickness


def calc_vol_heat_cap(density: float, spec_heat_cap: float) -> float:
    """
    Calculate volumetric heat capacity as the product of density and specific heat capacity.

    Parameters
    ----------
    density : float
        Density (kg/m³).
    spec_heat_cap : float
        Specific heat capacity (J/(kg·K)).

    Returns
    -------
    float
        Volumetric heat capacity (J/(m³·K)).
    """
    if density <= 0:
        raise ValueError("density must be positive")
    if spec_heat_cap <= 0:
        raise ValueError("spec_heat_cap must be positive")
    return spec_heat_cap * density


def calc_aq_vol_heat_cap(fluid_vol_heat_cap: float, rock_vol_heat_cap: float, porosity: float) -> float:
    """
    Calculate aquifer volumetric heat capacity as a porosity-weighted sum of fluid and rock volumetric heat capacities.

    Parameters
    ----------
    fluid_vol_heat_cap : float
        Volumetric heat capacity of the fluid (J/(m³·K)).
    rock_vol_heat_cap : float
        Volumetric heat capacity of the rock (J/(m³·K)).
    porosity : float
        Porosity of the aquifer (dimensionless, between 0 and 1).

    Returns
    -------
    float
        Aquifer volumetric heat capacity (J/(m³·K)).
    """
    if fluid_vol_heat_cap <= 0:
        raise ValueError("fluid_vol_heat_cap must be positive")
    if rock_vol_heat_cap <= 0:
        raise ValueError("rock_vol_heat_cap must be positive")
    if not (0 <= porosity <= 1):
        raise ValueError("porosity must be between 0 and 1")
    return porosity * fluid_vol_heat_cap + (1 - porosity) * rock_vol_heat_cap


def calc_darcy_velo(hydr_cond: float, hydr_grad: float) -> float:
    """
    Calculate Darcy velocity as the product of hydraulic conductivity and hydraulic gradient.

    Parameters
    ----------
    hydr_cond : float
        Hydraulic conductivity (m/s).
    hydr_grad : float
        Hydraulic gradient (dimensionless).

    Returns
    -------
    float
        Darcy (specific discharge) velocity (m/s).

    Notes
    -----
    This function does not enforce a sign convention for ``hydr_grad``. Many
    callers treat gradients as non-negative magnitudes.
    """
    if hydr_cond <= 0:
        raise ValueError("hydr_cond must be positive")
    return hydr_cond * hydr_grad


def calc_pore_velo(darcy_velo: float, porosity: float) -> float:
    """
    Calculate pore velocity as the Darcy velocity divided by porosity.

    Parameters
    ----------
    darcy_velo : float
        Darcy (specific discharge) velocity (m/s).
    porosity : float
        Porosity of the aquifer (dimensionless, between 0 and 1).

    Returns
    -------
    float
        Pore (seepage) velocity (m/s).
    """
    if porosity <= 0 or porosity >= 1:
        raise ValueError("porosity must be between 0 and 1")
    return darcy_velo / porosity


def calc_retard_fact(
    fluid_vol_heat_cap: float,
    aq_vol_heat_cap: float,
    porosity: float,
) -> float:
    """
    Calculate thermal retardation factor as the product of porosity and fluid volumetric heat capacity, divided by
    the aquifer volumetric heat capacity. The retardation factor describes the delay in thermal front propagation due to
    heat storage in the aquifer matrix.

    Parameters
    ----------
    fluid_vol_heat_cap : float
        Volumetric heat capacity of the fluid (J/(m³·K)).
    aq_vol_heat_cap : float
        Volumetric heat capacity of the aquifer (J/(m³·K)).
    porosity : float
        Porosity of the aquifer (dimensionless, between 0 and 1).

    Returns
    -------
    float
        Thermal retardation factor (dimensionless).
    """
    if fluid_vol_heat_cap <= 0:
        raise ValueError("fluid_vol_heat_cap must be positive")
    if aq_vol_heat_cap <= 0:
        raise ValueError("aq_vol_heat_cap must be positive")
    if porosity <= 0 or porosity >= 1:
        raise ValueError("porosity must be between 0 and 1")
    return (porosity * fluid_vol_heat_cap) / aq_vol_heat_cap


def calc_therm_front_velo(pore_velo: float, retard_fact: float) -> float:
    """
    Calculate thermal front velocity.

    In this implementation, thermal front velocity is defined as:

    ``therm_front_velo = pore_velo * retard_fact``

    It describes the speed at which a thermal front propagates through the
    aquifer under the simplifying assumptions encoded by the chosen retardation
    factor definition.

    Parameters
    ----------
    pore_velo : float
        Pore (seepage) velocity (m/s).
    retard_fact : float
        Thermal retardation factor (dimensionless).

    Returns
    -------
    float
        Thermal front velocity (m/s).
    """
    if pore_velo < 0:
        raise ValueError("pore_velo must be non-negative")
    if retard_fact <= 0:
        raise ValueError("retard_fact must be positive")
    return pore_velo * retard_fact


def calc_max_vol_flow_rate(
    well_radius: float,
    well_distance: float,
    max_drawdown: float,
    hydr_trans: float,
    storativity: float,
    duration: float,
) -> float:
    """
    Calculate a maximum volumetric flow rate based on a drawdown constraint.

    The flow rate is derived from the requirement that the drawdown at the well
    boundary of the extraction well exactly matches the maximum allowable
    drawdown. This drawdown
    drawdown at the well boundary of the extraction well exactly matches the maximum allowable drawdown. This drawdown
    is calculated as a superposition of the "drawdown from extraction" and "lift from reinjection" effects, evaluated
    at the well boundary of the extraction well. The two effects are calculated based on the Theis equation:
        Delta s = (Q / (4 * pi * T)) * W(u),  u = (r^2 * S) / (4 * T * t)
    where W(u) = -Ei(-u) is the well function, and Ei is the exponential integral function. Delta s is the lift
    (positive) or drawdown (negative), Q is the volumetric flow rate (positive for injection), negative for extraction),
    T is the hydraulic transmissivity, r is the radial distance from the injection or extraction well, S is the
    storativity, and t is the injection/extraction duration. For more details, see Theis:
    'The relation between the lowering of the piezometric surface and the rate and duration of a pumping well', 1935.

    Parameters
    ----------
    well_radius : float
        Radius of the well (m).
    well_distance : float
        Distance between wells (m).
    max_drawdown : float
        Maximum allowable drawdown (m).
    hydr_trans : float
        Hydraulic transmissivity (m²/s).
    storativity : float
        Storativity (-).
    duration: float
        Duration of the pumping period (s).

    Returns
    -------
    float
        Maximum volumetric flow rate (m³/s).

    Notes
    -----
    The same formula is used for heating and cooling in the analysis service;
    the difference comes from providing a different ``duration``.
    """
    if well_radius <= 0:
        raise ValueError("well_radius must be positive")
    if well_distance <= 0:
        raise ValueError("well_distance must be positive")
    if max_drawdown <= 0:
        raise ValueError("max_drawdown must be positive")
    if hydr_trans <= 0:
        raise ValueError("hydr_trans must be positive")
    if storativity <= 0 or storativity >= 1:
        raise ValueError("storativity must be between 0 and 1")
    if well_distance <= 2 * well_radius:
        raise ValueError("well_distance must be at least twice the well_radius")
    if duration <= 0:
        raise ValueError("duration must be positive")

    wf_arg_extr = (well_radius**2 * storativity) / (4 * hydr_trans * duration)
    wf_arg_inj = ((well_distance - well_radius) ** 2 * storativity) / (4 * hydr_trans * duration)
    wf_val_extr = -expi(-wf_arg_extr)
    wf_val_inj = -expi(-wf_arg_inj)
    max_vol_flow_rate = (4 * math.pi * hydr_trans * max_drawdown) / (wf_val_extr - wf_val_inj)
    return max_vol_flow_rate


def calc_mass_flow_rate(max_vol_flow_rate: float, fluid_density: float) -> float:
    """
    Calculate maximum mass flow rate as a product of maximum volumetric flow rate and fluid density.

    Parameters
    ----------
    max_vol_flow_rate : float
        Maximum volumetric flow rate (m³/s).
    fluid_density : float
        Density of the fluid (kg/m³).

    Returns
    -------
    float
        Maximum mass flow rate (kg/s).
    """
    if max_vol_flow_rate <= 0:
        raise ValueError("max_vol_flow_rate must be positive")
    if fluid_density <= 0:
        raise ValueError("fluid_density must be positive")
    return max_vol_flow_rate * fluid_density


def calc_therm_rate(mass_flow_rate: float, spec_heat_cap: float, temp_diff: float) -> float:
    """
    Calculate thermal rate based on mass flow rate, specific heat capacity, and temperature difference.

    Parameters
    ----------
    mass_flow_rate : float
        Mass flow rate (kg/s).
    spec_heat_cap : float
        Specific heat capacity (J/(kg·K)).
    temp_diff : float
        Temperature difference (K).

    Returns
    -------
    float
        Maximum thermal rate (W).
    """
    if mass_flow_rate <= 0:
        raise ValueError("mass_flow_rate must be positive")
    if spec_heat_cap <= 0:
        raise ValueError("spec_heat_cap must be positive")
    if temp_diff <= 0:
        raise ValueError("temp_diff must be positive")
    return mass_flow_rate * spec_heat_cap * temp_diff


def calc_therm_rad_voleq(
    fluid_vol_heat_cap: float, aq_vol_heat_cap: float, vol_inj_rate: float, duration: float, thickness: float
) -> float:
    """
    Calculate the volumetric-equivalent thermal radius.

    This is the radius of a theoretical cylindrical aquifer volume (height equal
    to aquifer thickness) that contains the same total thermal energy as the
    injected fluid volume over the given duration.

    Based on Doughty et al., "A dimensionless parameter approach to the thermal
    behavior of an aquifer thermal energy storage system" (1982).

    Parameters
    ----------
    fluid_vol_heat_cap : float
        Volumetric heat capacity of the fluid (J/(m³·K)).
    aq_vol_heat_cap : float
        Volumetric heat capacity of the aquifer, defined as the porosity-weighted average of the solid matrix and fluid
        volumetric heat capacities (J/(m³·K)).
    vol_inj_rate : float
        Constant volumetric injection rate (m³/s).
    duration : float
        Duration of the injection period (s).
    thickness : float
        Thickness of the aquifer (m).

    Returns
    -------
    float
        Volumetric-equivalent thermal radius (m).
    """

    therm_rad_voleq = math.sqrt(
        (fluid_vol_heat_cap * vol_inj_rate * duration) / (aq_vol_heat_cap * math.pi * thickness)
    )
    return therm_rad_voleq


def calc_therm_rad_adv(
    therm_front_velo: float,
    duration: float,
) -> float:
    """
    Calculate the advective thermal radius of a well after a given injection duration. The advective thermal radius
    describes the distance that a thermal front has propagated from the well due to advection alone.

    Parameters
    ----------
    therm_front_velo : float
        Absolute value of thermal front velocity (m/s).
    duration : float
        Duration of the heating or cooling period (s).

    Returns
    -------
    float
        Advective thermal radius (m).
    """
    if therm_front_velo < 0:
        raise ValueError("therm_front_velo must be non-negative")
    if duration <= 0:
        raise ValueError("duration must be positive")
    return therm_front_velo * duration


def calc_therm_rad(
    therm_rad_voleq: float,
    therm_rad_adv: float,
) -> float:
    """
    Calculate the combined thermal radius of a well after a given injection duration. The combined thermal radius
    accounts for both advective and conductive heat transport mechanisms, and is calculated as the sum of the
    volumetric-equivalent thermal radius and the advective thermal radius.

    Parameters
    ----------
    therm_rad_voleq : float
        Volumetric-equivalent thermal radius (m).
    therm_rad_adv : float
        Advective thermal radius (m).

    Returns
    -------
    float
        Combined thermal radius (m).
    """
    if therm_rad_voleq < 0:
        raise ValueError("therm_rad_voleq must be non-negative")
    if therm_rad_adv < 0:
        raise ValueError("therm_rad_adv must be non-negative")
    return therm_rad_voleq + therm_rad_adv


def calc_therm_area(
    therm_rad_warm_well: float,
    therm_rad_cold_well: float,
    well_distance: float,
) -> float:
    """
    Calculate the thermally relevant area of a well doublet system based on the thermal radii of the warm and cold
    wells, and the distance between the wells. It is calculated as the smallest enclosing rectangle of both wells'
    thermal circles.

    Parameters
    ----------
    therm_rad_warm_well : float
        Combined thermal radius of the warm well (m).
    therm_rad_cold_well : float
        Combined thermal radius of the cold well (m).
    well_distance : float
        Distance between wells (m).

    Returns
    -------
    float
        Thermally relevant area of the well doublet system (m²).
    """
    if therm_rad_warm_well < 0:
        raise ValueError("therm_rad_warm_well must be non-negative")
    if therm_rad_cold_well < 0:
        raise ValueError("therm_rad_cold_well must be non-negative")
    if well_distance <= 0:
        raise ValueError("well_distance must be positive")
    return (well_distance + therm_rad_warm_well + therm_rad_cold_well) * max(therm_rad_warm_well, therm_rad_cold_well)


def calc_therm_density(
    therm_rate: float,
    therm_area: float,
) -> float:
    """
    Calculate thermal density as thermal rate divided by the thermally relevant area of a well doublet system.

    Parameters
    ----------
    therm_rate : float
        Thermal rate (W).
    therm_area : float
        Thermally relevant area of a well doublet system (m²).

    Returns
    -------
    float
        Thermal density (W/m²).
    """
    if therm_rate <= 0:
        raise ValueError("therm_rate must be positive")
    if therm_area <= 0:
        raise ValueError("therm_area must be positive")
    return therm_rate / therm_area
