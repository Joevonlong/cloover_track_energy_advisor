"""Health endpoint integration test — proves the app boots.

Owner: Zhou (backend)
Feature ID: F01 (monorepo scaffold)
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    """GET /health returns 200 and the ok status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "heimwende-api"}
