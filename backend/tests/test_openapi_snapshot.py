import json
from pathlib import Path

from fastapi.testclient import TestClient

from geoninja_backend.main import app

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"


def _normalize(obj):
    # stable ordering so diffs are meaningful
    return json.loads(json.dumps(obj, sort_keys=True, ensure_ascii=False))


def test_openapi_matches_snapshot():
    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    current = _normalize(resp.json())

    assert CONTRACT_PATH.exists(), f"Missing snapshot at {CONTRACT_PATH}. " "Generate it once and commit it."

    expected = _normalize(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))

    assert current == expected, (
        "OpenAPI snapshot mismatch. If this change is intentional, "
        "overwrite contracts/openapi.json with the new /openapi.json and commit."
    )
