"""Rock properties lookup service.

This module loads a small reference table of representative bulk rock
thermophysical properties keyed by GLiM lithology codes.

Data source
-----------
The CSV file is staged by the data pipeline step
``data_pipeline.scripts.dp_rock_properties`` and is expected at:

    ``backend/data/rock_properties.csv``

The file is intentionally treated as a simple lookup table. The backend uses it
to derive local parameters such as `rockDensity`, `rockSpecHeatCap`, and
`rockThermCond`.

Caching
-------
The CSV is loaded once per process using ``lru_cache(maxsize=1)``.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from geoninja_backend.services.glim_lookup import GlimLithoKey

log = logging.getLogger(__name__)

_ROCK_PROPERTIES_FILE = (Path(__file__).parents[3] / "data" / "rock_properties.csv").resolve()


@dataclass(frozen=True)
class RockProperties:
    """Representative bulk thermophysical rock properties.

    Attributes:
        density: Density in kg/m³.
        spec_heat_cap: Specific heat capacity in J/(kg·K).
        therm_cond: Thermal conductivity in W/(m·K).
    """

    density: float  # kg/m³
    spec_heat_cap: float  # J/(kg·K)
    therm_cond: float  # W/(m·K)


@lru_cache(maxsize=1)
def load_rock_properties_by_litho_key() -> dict[GlimLithoKey, RockProperties]:
    """Load rock properties from CSV.

    Returns:
        Mapping of :class:`~geoninja_backend.services.glim_lookup.GlimLithoKey` to
        :class:`RockProperties`.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing, numeric conversion fails, or
            duplicate/unknown lithology keys are encountered.

    Notes:
        The result is cached at the process level.
    """
    if not _ROCK_PROPERTIES_FILE.exists():
        log.critical("Rock properties file not found at %s", _ROCK_PROPERTIES_FILE)
        raise FileNotFoundError(f"Rock properties file not found at {_ROCK_PROPERTIES_FILE}")

    log.info("Loading rock properties from %s", _ROCK_PROPERTIES_FILE)

    properties: dict[GlimLithoKey, RockProperties] = {}

    with _ROCK_PROPERTIES_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_columns = {
            "litho_key",
            "density_kg_m3",
            "spec_heat_cap_j_kgK",
            "therm_cond_w_mK",
        }

        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Rock properties CSV missing columns: {sorted(missing)}")

        for row in reader:
            try:
                litho = GlimLithoKey(row["litho_key"])
            except ValueError:
                raise ValueError(f"Unknown litho_key '{row['litho_key']}' in rock_properties.csv") from None

            try:
                props = RockProperties(
                    density=float(row["density_kg_m3"]),
                    spec_heat_cap=float(row["spec_heat_cap_j_kgK"]),
                    therm_cond=float(row["therm_cond_w_mK"]),
                )
            except ValueError as e:
                raise ValueError(f"Invalid numeric value for litho_key '{row['litho_key']}': {e}") from e

            if litho in properties:
                raise ValueError(f"Duplicate litho_key '{litho.value}' in rock_properties.csv")

            properties[litho] = props

    log.info("Loaded rock properties for %d lithology classes", len(properties))
    return properties


def get_rock_properties(litho: GlimLithoKey) -> RockProperties:
    """Return rock properties for a given GLiM lithology key.

    Args:
        litho: GLiM lithology key.

    Returns:
        The corresponding :class:`RockProperties` instance.

    Raises:
        KeyError: If properties are not defined for the given lithology.
    """
    props_by_litho = load_rock_properties_by_litho_key()

    try:
        return props_by_litho[litho]
    except KeyError:
        raise KeyError(f"No rock properties defined for lithology '{litho.value}'") from None
