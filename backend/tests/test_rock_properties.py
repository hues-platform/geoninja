from __future__ import annotations

from pathlib import Path

import pytest

import geoninja_backend.services.rock_properties as rock_properties
from geoninja_backend.services.glim_lookup import GlimLithoKey
from geoninja_backend.services.rock_properties import RockProperties


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _set_csv(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setattr(rock_properties, "_ROCK_PROPERTIES_FILE", path)
    rock_properties.load_rock_properties_by_litho_key.cache_clear()


def test_load_rock_properties_by_litho_key_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "rock_properties.csv"
    _write_csv(
        csv_path,
        "litho_key,density_kg_m3,spec_heat_cap_j_kgK,therm_cond_w_mK\n" "su,2000,900,1.2\n" "sc,2700,850,2.1\n",
    )
    _set_csv(monkeypatch, csv_path)

    props = rock_properties.load_rock_properties_by_litho_key()

    assert set(props.keys()) == {GlimLithoKey.UNCONSOLIDATED_SEDIMENTS, GlimLithoKey.CARBONATE_SEDIMENTARY_ROCKS}
    assert props[GlimLithoKey.UNCONSOLIDATED_SEDIMENTS] == RockProperties(
        density=2000.0,
        spec_heat_cap=900.0,
        therm_cond=1.2,
    )


def test_load_rock_properties_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "does_not_exist.csv"
    _set_csv(monkeypatch, missing)

    with pytest.raises(FileNotFoundError, match=r"Rock properties file not found"):
        rock_properties.load_rock_properties_by_litho_key()


def test_load_rock_properties_missing_columns_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "rock_properties.csv"
    _write_csv(csv_path, "litho_key,density_kg_m3\nsu,2000\n")
    _set_csv(monkeypatch, csv_path)

    with pytest.raises(ValueError, match=r"missing columns"):
        rock_properties.load_rock_properties_by_litho_key()


def test_load_rock_properties_unknown_litho_key_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "rock_properties.csv"
    _write_csv(
        csv_path,
        "litho_key,density_kg_m3,spec_heat_cap_j_kgK,therm_cond_w_mK\n" "xx,2000,900,1.2\n",
    )
    _set_csv(monkeypatch, csv_path)

    with pytest.raises(ValueError, match=r"Unknown litho_key 'xx'"):
        rock_properties.load_rock_properties_by_litho_key()


def test_load_rock_properties_invalid_numeric_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "rock_properties.csv"
    _write_csv(
        csv_path,
        "litho_key,density_kg_m3,spec_heat_cap_j_kgK,therm_cond_w_mK\n" "su,not-a-number,900,1.2\n",
    )
    _set_csv(monkeypatch, csv_path)

    with pytest.raises(ValueError, match=r"Invalid numeric value"):
        rock_properties.load_rock_properties_by_litho_key()


def test_load_rock_properties_duplicate_litho_key_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "rock_properties.csv"
    _write_csv(
        csv_path,
        "litho_key,density_kg_m3,spec_heat_cap_j_kgK,therm_cond_w_mK\n" "su,2000,900,1.2\n" "su,2100,910,1.3\n",
    )
    _set_csv(monkeypatch, csv_path)

    with pytest.raises(ValueError, match=r"Duplicate litho_key 'su'"):
        rock_properties.load_rock_properties_by_litho_key()


def test_get_rock_properties_returns_item_or_raises_keyerror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "rock_properties.csv"
    _write_csv(
        csv_path,
        "litho_key,density_kg_m3,spec_heat_cap_j_kgK,therm_cond_w_mK\n" "su,2000,900,1.2\n",
    )
    _set_csv(monkeypatch, csv_path)

    item = rock_properties.get_rock_properties(GlimLithoKey.UNCONSOLIDATED_SEDIMENTS)
    assert item.density == 2000.0

    with pytest.raises(KeyError, match=r"No rock properties defined for lithology 'wb'"):
        rock_properties.get_rock_properties(GlimLithoKey.WATER_BODIES)
