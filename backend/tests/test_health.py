from fastapi.testclient import TestClient

from geoninja_backend.main import app


def test_openapi_available():
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
