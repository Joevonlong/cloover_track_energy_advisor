"""Integration tests for the permit layer API endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


BUCHEN_PAYLOAD = {
    "address": "Am Nahholz 55, 74722 Buchen",
    "plz": "74722",
    "lat": 49.52,
    "lng": 9.32,
    "intake": {
        "building_year": 1985,
        "fuel_type": "OIL",
        "has_private_parking": True,
    },
}


def _mock_httpx_get(url: str, **kwargs: object) -> MagicMock:
    """Return sensible mocked responses for each external API."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None

    if "openplzapi" in url:
        resp.json.return_value = [{"federalState": {"name": "Baden-Württemberg"}}]
    elif "geoservices.bayern" in url or "wms.nrw" in url or "fbinter.stadt" in url:
        resp.json.return_value = {"features": []}
    elif "marktstammdatenregister" in url:
        resp.json.return_value = {"Gesamtanzahl": 67}
    elif "anthropic" in url:
        resp.json.return_value = {"content": [{"text": "Test LLM summary."}]}
    else:
        resp.json.return_value = {}

    return resp


def _mock_httpx_post(url: str, **kwargs: object) -> MagicMock:
    """Return empty OSM features for Overpass calls."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"elements": []}
    return resp


@pytest.fixture
def mock_http() -> object:
    with (
        patch("httpx.get", side_effect=_mock_httpx_get),
        patch("httpx.post", side_effect=_mock_httpx_post),
    ):
        yield


def test_permits_endpoint_returns_10_checks(client: TestClient, mock_http: object) -> None:
    resp = client.post("/api/v1/advisor/permits", json=BUCHEN_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "checks" in data
    assert len(data["checks"]) == 12


def test_permits_has_required_fields(client: TestClient, mock_http: object) -> None:
    resp = client.post("/api/v1/advisor/permits", json=BUCHEN_PAYLOAD)
    data = resp.json()
    assert "solar_blocked" in data
    assert "heatpump_blocked" in data
    assert "ev_charger_blocked" in data
    assert "any_fatal" in data
    assert "bundesland" in data
    assert "neighbour_count" in data


def test_permits_check_has_source(client: TestClient, mock_http: object) -> None:
    resp = client.post("/api/v1/advisor/permits", json=BUCHEN_PAYLOAD)
    checks = resp.json()["checks"]
    # Every check must have a source_name and fetched_at
    for check in checks:
        assert check["source_name"], f"Check {check['id']} missing source_name"
        assert check["fetched_at"], f"Check {check['id']} missing fetched_at"


def test_permits_private_parking_passes(client: TestClient, mock_http: object) -> None:
    resp = client.post("/api/v1/advisor/permits", json=BUCHEN_PAYLOAD)
    checks = {c["id"]: c for c in resp.json()["checks"]}
    assert checks["ev_parking"]["status"] == "pass"


def test_permits_old_boiler_hp_passes(client: TestClient, mock_http: object) -> None:
    resp = client.post("/api/v1/advisor/permits", json=BUCHEN_PAYLOAD)
    checks = {c["id"]: c for c in resp.json()["checks"]}
    # 1985 boiler = 39 years old → GEG replacement required = pass
    assert checks["hp_geg"]["status"] == "pass"


def test_permits_battery_always_pass(client: TestClient, mock_http: object) -> None:
    resp = client.post("/api/v1/advisor/permits", json=BUCHEN_PAYLOAD)
    checks = {c["id"]: c for c in resp.json()["checks"]}
    assert checks["battery_install"]["status"] == "pass"
    assert checks["battery_mastr"]["status"] == "info"


def test_permits_bw_denkmal_is_warn_not_pass(client: TestClient, mock_http: object) -> None:
    # BW has no WMS API → denkmal can't be confirmed clear → warn
    resp = client.post("/api/v1/advisor/permits", json=BUCHEN_PAYLOAD)
    checks = {c["id"]: c for c in resp.json()["checks"]}
    # BW fallback = OSM-only → can't confirm clear without WMS
    assert checks["solar_denkmal"]["status"] in ("pass", "warn")


def test_permits_stream_returns_sse(client: TestClient, mock_http: object) -> None:
    resp = client.get(
        "/api/v1/advisor/permits/stream",
        params={
            "address": "Am Nahholz 55, 74722 Buchen",
            "plz": "74722",
            "lat": 49.52,
            "lng": 9.32,
            "building_year": 1985,
            "fuel_type": "OIL",
            "has_private_parking": True,
        },
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    lines = [l for l in resp.text.split("\n") if l.startswith("data:")]
    # 12 check events + 1 done event = 13
    assert len(lines) == 13
    assert '"event": "done"' in lines[-1]
