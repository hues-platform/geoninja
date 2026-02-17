import math

import pytest
from scipy.special import expi

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


def test_calc_hydr_trans_product():
    assert calc_hydr_trans(2.0e-5, 10.0) == pytest.approx(2.0e-4)


@pytest.mark.parametrize(
    "hydr_cond, thickness",
    [
        (0.0, 1.0),
        (-1.0, 1.0),
        (1.0, 0.0),
        (1.0, -1.0),
    ],
)
def test_calc_hydr_trans_validates_inputs(hydr_cond: float, thickness: float):
    with pytest.raises(ValueError):
        calc_hydr_trans(hydr_cond, thickness)


def test_calc_vol_heat_cap_product():
    assert calc_vol_heat_cap(1000.0, 4184.0) == pytest.approx(4_184_000.0)


@pytest.mark.parametrize("density, spec_heat_cap", [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)])
def test_calc_vol_heat_cap_validates_inputs(density: float, spec_heat_cap: float):
    with pytest.raises(ValueError):
        calc_vol_heat_cap(density, spec_heat_cap)


def test_calc_aq_vol_heat_cap_porosity_weighted_sum():
    fluid = 4.0
    rock = 2.0
    porosity = 0.25
    expected = porosity * fluid + (1.0 - porosity) * rock
    assert calc_aq_vol_heat_cap(fluid, rock, porosity) == pytest.approx(expected)


@pytest.mark.parametrize("porosity", [-0.01, 1.01])
def test_calc_aq_vol_heat_cap_rejects_out_of_range_porosity(porosity: float):
    with pytest.raises(ValueError):
        calc_aq_vol_heat_cap(1.0, 1.0, porosity)


def test_calc_darcy_velo_allows_negative_gradient():
    # Implementation does not enforce a sign convention for hydr_grad.
    assert calc_darcy_velo(2.0, -0.5) == pytest.approx(-1.0)


def test_calc_pore_velo_divides_by_porosity():
    assert calc_pore_velo(1.0e-6, 0.25) == pytest.approx(4.0e-6)


@pytest.mark.parametrize("porosity", [0.0, 1.0, -0.1, 1.1])
def test_calc_pore_velo_validates_porosity(porosity: float):
    with pytest.raises(ValueError):
        calc_pore_velo(1.0, porosity)


def test_calc_retard_fact_formula():
    # (porosity * fluid) / aq
    assert calc_retard_fact(fluid_vol_heat_cap=4.0, aq_vol_heat_cap=8.0, porosity=0.5) == pytest.approx(0.25)


@pytest.mark.parametrize(
    "fluid_vol_heat_cap, aq_vol_heat_cap, porosity",
    [
        (0.0, 1.0, 0.5),
        (-1.0, 1.0, 0.5),
        (1.0, 0.0, 0.5),
        (1.0, -1.0, 0.5),
        (1.0, 1.0, 0.0),
        (1.0, 1.0, 1.0),
    ],
)
def test_calc_retard_fact_validates_inputs(fluid_vol_heat_cap: float, aq_vol_heat_cap: float, porosity: float):
    with pytest.raises(ValueError):
        calc_retard_fact(fluid_vol_heat_cap, aq_vol_heat_cap, porosity)


def test_calc_therm_front_velo_product():
    assert calc_therm_front_velo(pore_velo=2.0, retard_fact=0.25) == pytest.approx(0.5)


@pytest.mark.parametrize("pore_velo, retard_fact", [(-1.0, 0.5), (1.0, 0.0), (1.0, -1.0)])
def test_calc_therm_front_velo_validates_inputs(pore_velo: float, retard_fact: float):
    with pytest.raises(ValueError):
        calc_therm_front_velo(pore_velo, retard_fact)


def test_calc_max_vol_flow_rate_matches_formula():
    # Pick stable, physically plausible inputs.
    well_radius = 0.1
    well_distance = 10.0
    max_drawdown = 5.0
    hydr_trans = 2.0e-4
    storativity = 0.1
    duration = 120.0 * 24.0 * 3600.0  # 120 days

    # Expected value using the documented formula.
    wf_arg_extr = (well_radius**2 * storativity) / (4 * hydr_trans * duration)
    wf_arg_inj = ((well_distance - well_radius) ** 2 * storativity) / (4 * hydr_trans * duration)
    wf_val_extr = -expi(-wf_arg_extr)
    wf_val_inj = -expi(-wf_arg_inj)
    expected = (4 * math.pi * hydr_trans * max_drawdown) / (wf_val_extr - wf_val_inj)

    assert calc_max_vol_flow_rate(
        well_radius=well_radius,
        well_distance=well_distance,
        max_drawdown=max_drawdown,
        hydr_trans=hydr_trans,
        storativity=storativity,
        duration=duration,
    ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "well_radius": 0.0,
            "well_distance": 10.0,
            "max_drawdown": 1.0,
            "hydr_trans": 1.0,
            "storativity": 0.1,
            "duration": 1.0,
        },
        {
            "well_radius": 0.1,
            "well_distance": 0.0,
            "max_drawdown": 1.0,
            "hydr_trans": 1.0,
            "storativity": 0.1,
            "duration": 1.0,
        },
        {
            "well_radius": 0.1,
            "well_distance": 0.1,
            "max_drawdown": 1.0,
            "hydr_trans": 1.0,
            "storativity": 0.1,
            "duration": 1.0,
        },  # too close
        {
            "well_radius": 0.1,
            "well_distance": 10.0,
            "max_drawdown": 0.0,
            "hydr_trans": 1.0,
            "storativity": 0.1,
            "duration": 1.0,
        },
        {
            "well_radius": 0.1,
            "well_distance": 10.0,
            "max_drawdown": 1.0,
            "hydr_trans": 0.0,
            "storativity": 0.1,
            "duration": 1.0,
        },
        {
            "well_radius": 0.1,
            "well_distance": 10.0,
            "max_drawdown": 1.0,
            "hydr_trans": 1.0,
            "storativity": 0.0,
            "duration": 1.0,
        },
        {
            "well_radius": 0.1,
            "well_distance": 10.0,
            "max_drawdown": 1.0,
            "hydr_trans": 1.0,
            "storativity": 1.0,
            "duration": 1.0,
        },
        {
            "well_radius": 0.1,
            "well_distance": 10.0,
            "max_drawdown": 1.0,
            "hydr_trans": 1.0,
            "storativity": 0.1,
            "duration": 0.0,
        },
    ],
)
def test_calc_max_vol_flow_rate_validates_inputs(kwargs: dict):
    with pytest.raises(ValueError):
        calc_max_vol_flow_rate(**kwargs)


def test_calc_mass_flow_rate_product():
    assert calc_mass_flow_rate(0.2, 1000.0) == pytest.approx(200.0)


@pytest.mark.parametrize("max_vol_flow_rate, fluid_density", [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)])
def test_calc_mass_flow_rate_validates_inputs(max_vol_flow_rate: float, fluid_density: float):
    with pytest.raises(ValueError):
        calc_mass_flow_rate(max_vol_flow_rate, fluid_density)


def test_calc_therm_rate_product():
    assert calc_therm_rate(mass_flow_rate=2.0, spec_heat_cap=4000.0, temp_diff=5.0) == pytest.approx(40_000.0)


@pytest.mark.parametrize(
    "mass_flow_rate, spec_heat_cap, temp_diff",
    [(0.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (1.0, 0.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 0.0), (1.0, 1.0, -1.0)],
)
def test_calc_therm_rate_validates_inputs(mass_flow_rate: float, spec_heat_cap: float, temp_diff: float):
    with pytest.raises(ValueError):
        calc_therm_rate(mass_flow_rate, spec_heat_cap, temp_diff)


def test_calc_therm_rad_voleq_formula():
    fluid_vol_heat_cap = 4.0
    aq_vol_heat_cap = 8.0
    vol_inj_rate = 0.1
    duration = 10.0
    thickness = 5.0

    expected = math.sqrt((fluid_vol_heat_cap * vol_inj_rate * duration) / (aq_vol_heat_cap * math.pi * thickness))
    assert calc_therm_rad_voleq(
        fluid_vol_heat_cap, aq_vol_heat_cap, vol_inj_rate, duration, thickness
    ) == pytest.approx(expected)


def test_calc_therm_rad_adv_product_and_validation():
    assert calc_therm_rad_adv(therm_front_velo=0.2, duration=10.0) == pytest.approx(2.0)

    with pytest.raises(ValueError):
        calc_therm_rad_adv(therm_front_velo=-0.1, duration=10.0)

    with pytest.raises(ValueError):
        calc_therm_rad_adv(therm_front_velo=0.1, duration=0.0)


def test_calc_therm_rad_sum_and_validation():
    assert calc_therm_rad(therm_rad_voleq=1.0, therm_rad_adv=2.0) == pytest.approx(3.0)

    with pytest.raises(ValueError):
        calc_therm_rad(therm_rad_voleq=-1.0, therm_rad_adv=0.0)

    with pytest.raises(ValueError):
        calc_therm_rad(therm_rad_voleq=0.0, therm_rad_adv=-1.0)


def test_calc_therm_area_matches_definition():
    warm = 2.0
    cold = 3.0
    dist = 10.0
    expected = (dist + warm + cold) * max(warm, cold)
    assert calc_therm_area(warm, cold, dist) == pytest.approx(expected)


@pytest.mark.parametrize("warm, cold, dist", [(-1.0, 1.0, 10.0), (1.0, -1.0, 10.0), (1.0, 1.0, 0.0)])
def test_calc_therm_area_validates_inputs(warm: float, cold: float, dist: float):
    with pytest.raises(ValueError):
        calc_therm_area(warm, cold, dist)


def test_calc_therm_density_rate_over_area():
    assert calc_therm_density(therm_rate=100.0, therm_area=25.0) == pytest.approx(4.0)


@pytest.mark.parametrize("therm_rate, therm_area", [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)])
def test_calc_therm_density_validates_inputs(therm_rate: float, therm_area: float):
    with pytest.raises(ValueError):
        calc_therm_density(therm_rate, therm_area)
