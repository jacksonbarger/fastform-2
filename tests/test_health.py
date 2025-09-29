from fastapi.testclient import TestClient

from fastform.api.app import app


def test_health_ok():
    with TestClient(app) as c:
        assert c.get("/v1/health").json() == {"status": "ok"}
