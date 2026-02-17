from __future__ import annotations

from datetime import date

import pytest

from geoninja_backend.services.param_access import (
    ParamValidationError,
    get_date_from_key_value_dict,
    get_float_from_key_value_dict,
    get_int_from_key_value_dict,
    get_param_def_from_registry,
    get_string_from_key_value_dict,
)


def test_get_param_def_from_registry_unknown_key_raises() -> None:
    with pytest.raises(ParamValidationError, match=r"Unknown parameter key"):
        get_param_def_from_registry("notARealKey")


def test_get_float_from_key_value_dict_happy_path_returns_float() -> None:
    params: dict[str, float | str] = {"porosity": 0.2}
    assert get_float_from_key_value_dict(params, "porosity") == 0.2


def test_get_float_from_key_value_dict_missing_key_raises() -> None:
    with pytest.raises(ParamValidationError, match=r"Missing required parameter 'porosity'"):
        get_float_from_key_value_dict({}, "porosity")


def test_get_float_from_key_value_dict_wrong_value_type_raises() -> None:
    params: dict[str, float | str] = {"porosity": "0.2"}
    with pytest.raises(ParamValidationError, match=r"must be a number"):
        get_float_from_key_value_dict(params, "porosity")


def test_get_float_from_key_value_dict_value_type_mismatch_raises() -> None:
    params: dict[str, float | str] = {"rockType": "sandstone"}
    with pytest.raises(ParamValidationError, match=r"is not of type 'number'"):
        get_float_from_key_value_dict(params, "rockType")


def test_get_float_from_key_value_dict_enforces_min_max() -> None:
    with pytest.raises(ParamValidationError, match=r"below min"):
        get_float_from_key_value_dict({"porosity": 0.0}, "porosity")

    with pytest.raises(ParamValidationError, match=r"above max"):
        get_float_from_key_value_dict({"porosity": 0.6}, "porosity")

    assert get_float_from_key_value_dict({"porosity": 0.01}, "porosity") == 0.01
    assert get_float_from_key_value_dict({"porosity": 0.5}, "porosity") == 0.5


def test_get_int_from_key_value_dict_happy_path_and_integer_semantics() -> None:
    assert get_int_from_key_value_dict({"year": 2020}, "year") == 2020
    assert get_int_from_key_value_dict({"year": 2020.0}, "year") == 2020

    with pytest.raises(ParamValidationError, match=r"must be an integer"):
        get_int_from_key_value_dict({"year": 2020.5}, "year")


def test_get_int_from_key_value_dict_enforces_registry_bounds() -> None:
    with pytest.raises(ParamValidationError, match=r"below min"):
        get_int_from_key_value_dict({"year": 1989}, "year")

    with pytest.raises(ParamValidationError, match=r"above max"):
        get_int_from_key_value_dict({"year": 2024}, "year")


def test_get_string_from_key_value_dict_required_optional() -> None:
    assert get_string_from_key_value_dict({"rockType": "granite"}, "rockType") == "granite"

    with pytest.raises(ParamValidationError, match=r"Missing required parameter 'rockType'"):
        get_string_from_key_value_dict({}, "rockType")

    assert get_string_from_key_value_dict({}, "rockType", required=False) is None


def test_get_string_from_key_value_dict_type_checks_value_and_registry() -> None:
    with pytest.raises(ParamValidationError, match=r"must be a string"):
        get_string_from_key_value_dict({"rockType": 12.0}, "rockType")

    with pytest.raises(ParamValidationError, match=r"is not of type 'string'"):
        get_string_from_key_value_dict({"porosity": 0.2}, "porosity")


def test_get_date_from_key_value_dict_parses_dd_mm_and_optional_trailing_dot() -> None:
    params: dict[str, float | str] = {
        "heatPeriodStart": "01.02",
        "heatPeriodEnd": "01.02.",
    }

    assert get_date_from_key_value_dict(params, "heatPeriodStart", year=2020) == date(2020, 2, 1)
    assert get_date_from_key_value_dict(params, "heatPeriodEnd", year=2020) == date(2020, 2, 1)

    assert get_date_from_key_value_dict({"heatPeriodStart": " 01.02. "}, "heatPeriodStart", year=2020) == date(
        2020, 2, 1
    )


def test_get_date_from_key_value_dict_validates_required_and_types_and_format() -> None:
    with pytest.raises(ParamValidationError, match=r"Missing required parameter 'heatPeriodStart'"):
        get_date_from_key_value_dict({}, "heatPeriodStart", year=2020)

    with pytest.raises(ParamValidationError, match=r"must be a string"):
        get_date_from_key_value_dict({"heatPeriodStart": 1.0}, "heatPeriodStart", year=2020)

    with pytest.raises(ParamValidationError, match=r"must be in 'DD\.MM' format"):
        get_date_from_key_value_dict({"heatPeriodStart": "1/2"}, "heatPeriodStart", year=2020)


def test_get_date_from_key_value_dict_rejects_invalid_calendar_dates() -> None:
    with pytest.raises(ParamValidationError, match=r"Invalid date"):
        get_date_from_key_value_dict({"heatPeriodStart": "31.02"}, "heatPeriodStart", year=2020)


def test_get_date_from_key_value_dict_value_type_mismatch_raises() -> None:
    with pytest.raises(ParamValidationError, match=r"is not of type 'string'"):
        get_date_from_key_value_dict({"porosity": 0.2}, "porosity", year=2020)
