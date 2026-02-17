"""Parameter access and validation helpers.

This module provides convenience functions for extracting typed values from an
API-facing `params` mapping (typically `dict[str, float | str]`) while enforcing
constraints from the backend parameter registry.

Registry coupling
-----------------
Validation is driven by :data:`geoninja_backend.core.param_registry.PARAM_REGISTRY`.
That registry is validated against the shared contract file `contracts/params.json`.

All public helpers raise :class:`ParamValidationError` on missing keys, type
mismatches, or min/max constraint violations.
"""

from __future__ import annotations

from datetime import date

from geoninja_backend.core.param_registry import PARAM_REGISTRY, ParamDef, is_param_key


class ParamValidationError(ValueError):
    """Raised when request parameters are missing or invalid."""

    pass


def get_param_def_from_registry(key: str) -> ParamDef:
    """Return the parameter definition for a key.

    Raises:
        ParamValidationError: If the key is unknown.
    """
    if not is_param_key(key):
        raise ParamValidationError(f"Unknown parameter key: {key}")
    return PARAM_REGISTRY[key]


def get_float_from_key_value_dict(
    params: dict[str, float | str],  # Input dict of parameter key to value
    key: str,  # Parameter key to fetch, must be of type 'number'
) -> float:
    """Fetch and validate a numeric parameter as ``float``.

    This enforces:
    - key exists in registry
    - registry `valueType` is `number`
    - value is an `int`/`float`
    - optional min/max constraints
    """
    return _get_numeric_raw(params, key)


def get_int_from_key_value_dict(
    params: dict[str, float | str],
    key: str,
) -> int:
    """Fetch and validate an integer-valued numeric parameter."""
    value = _get_numeric_raw(params, key)

    if not value.is_integer():
        raise ParamValidationError(f"Parameter '{key}' must be an integer, got {value}")

    return int(value)


def get_string_from_key_value_dict(
    params: dict[str, float | str],  # Input dict of parameter key to value
    key: str,  # Parameter key to fetch, must be of type 'string'
    required: bool = True,  # Whether the parameter is required
) -> str | None:
    """Fetch and validate a string parameter.

    Args:
        params: Mapping of key -> raw value.
        key: Parameter key to fetch (must be `valueType == "string"` in the registry).
        required: If ``False``, missing keys return ``None`` instead of raising.
    """
    # Get parameter definition and check value type
    pdef = get_param_def_from_registry(key)
    if pdef["valueType"] != "string":
        raise ParamValidationError(f"Parameter '{key}' is not of type 'string'")
    # Get raw value
    raw = params.get(key, None)

    # Check presence
    if raw is None:
        if required:
            raise ParamValidationError(f"Missing required parameter '{key}'")
        return None

    if not isinstance(raw, str):
        raise ParamValidationError(f"Parameter '{key}' must be a string, got {type(raw).__name__}")
    return raw


def get_date_from_key_value_dict(
    params: dict[str, float | str],
    key: str,
    year: int,
) -> date:
    """Fetch a date-like string and combine it with a year.

    The value is expected to be a string formatted as ``DD.MM`` or ``DD.MM.``.

    Args:
        params: Mapping of key -> raw value.
        key: Parameter key to fetch (must be `valueType == "string"`).
        year: Year to attach to the parsed day/month.

    Returns:
        A :class:`datetime.date` for the given year.
    """
    pdef = get_param_def_from_registry(key)

    if pdef["valueType"] != "string":
        raise ParamValidationError(f"Parameter '{key}' is not of type 'string'")

    raw = params.get(key, None)
    if raw is None:
        raise ParamValidationError(f"Missing required parameter '{key}'")

    if not isinstance(raw, str):
        raise ParamValidationError(f"Parameter '{key}' must be a string, got {type(raw).__name__}")

    s = raw.strip()

    # Allow optional trailing dot: "DD.MM."
    if s.endswith("."):
        s = s[:-1]

    parts = s.split(".")
    if len(parts) != 2:
        raise ParamValidationError(f"Parameter '{key}' must be in 'DD.MM' format, got '{raw}'")

    try:
        day = int(parts[0])
        month = int(parts[1])
        return date(year, month, day)
    except ValueError as e:
        raise ParamValidationError(f"Invalid date for parameter '{key}': '{raw}'") from e


def _get_numeric_raw(
    params: dict[str, float | str],
    key: str,
) -> float:
    """Fetch a numeric value and apply registry-based validation.

    Enforces presence, numeric type, and optional min/max constraints from the
    parameter definition.

    Returns:
        The numeric value as a float (integer semantics are not enforced here).
    """
    pdef = get_param_def_from_registry(key)

    if pdef["valueType"] != "number":
        raise ParamValidationError(f"Parameter '{key}' is not of type 'number'")

    raw = params.get(key, None)
    if raw is None:
        raise ParamValidationError(f"Missing required parameter '{key}'")

    if not isinstance(raw, int | float):
        raise ParamValidationError(f"Parameter '{key}' must be a number, got {type(raw).__name__}")

    value = float(raw)

    mn = pdef.get("min")
    mx = pdef.get("max")
    if mn is not None and value < mn:
        raise ParamValidationError(f"Parameter '{key}'={value} below min {mn}")
    if mx is not None and value > mx:
        raise ParamValidationError(f"Parameter '{key}'={value} above max {mx}")

    return value
