"""Google Solar + Geocoding — real roof data for any German address.

Call `roof_from_address()` to get a `RoofData` that feeds directly into
the pipeline's `max_modules` and `specific_yield` inputs.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_SOLAR_URL = "https://solar.googleapis.com/v1/buildingInsights:findClosest"

# Trina Vertex S+ 440W panel area (default panel in pipeline)
_DEFAULT_PANEL_AREA_M2 = 1.134 * 1.762

# Fallback when Google Solar has no coverage
_FALLBACK_USABLE_RATIO = 0.30   # 30% of floor area
_FALLBACK_SPECIFIC_YIELD = 950.0  # kWh/kWp/yr, Germany average


class GoogleSolarError(Exception):
    pass


@dataclass
class RoofData:
    """Roof geometry + solar potential from Google Solar API (or fallback)."""
    max_modules: int
    usable_area_m2: float
    dominant_orientation: str          # "S" | "SE" | "SW" | "E" | "W" | "N"
    specific_yield_kwh_per_kwp: float  # kWh/kWp/yr — pass to pipeline as specific_yield
    source: str                        # "google_solar" | "floor_area_fallback"
    lat: float
    lng: float


def _azimuth_to_orientation(deg: float) -> str:
    deg = deg % 360
    if deg < 67.5 or deg >= 292.5:
        return "N"
    if deg < 112.5:
        return "E"
    if deg < 157.5:
        return "SE"
    if deg < 202.5:
        return "S"
    if deg < 247.5:
        return "SW"
    return "W"


def geocode(address: str, api_key: str) -> tuple[float, float]:
    """Return (lat, lng) for an address via Google Geocoding API."""
    resp = httpx.get(
        _GEOCODING_URL,
        params={"address": address, "key": api_key},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        raise GoogleSolarError(f"Geocoding failed ({data.get('status')}): {address!r}")
    loc = data["results"][0]["geometry"]["location"]
    return float(loc["lat"]), float(loc["lng"])


def _fetch_building_insights(lat: float, lng: float, api_key: str) -> dict:
    resp = httpx.get(
        _SOLAR_URL,
        params={
            "location.latitude": lat,
            "location.longitude": lng,
            "requiredQuality": "LOW",
            "key": api_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()  # type: ignore[no-any-return]


def _dominant_orientation(roof_segment_stats: list[dict]) -> str:
    """Orientation of the largest south-facing segment (fallback: largest overall)."""
    south = [s for s in roof_segment_stats if 90 <= s.get("azimuthDegrees", 0) <= 270]
    pool = south or roof_segment_stats
    if not pool:
        return "S"
    best = max(pool, key=lambda s: s.get("stats", {}).get("areaMeters2", 0))
    return _azimuth_to_orientation(best.get("azimuthDegrees", 180))


def _specific_yield_from_configs(solar_potential: dict, panel_count: int) -> float:
    """kWh/kWp/yr derived from Google's solarPanelConfigs for our panel count."""
    configs = solar_potential.get("solarPanelConfigs", [])
    if not configs:
        return _FALLBACK_SPECIFIC_YIELD
    panel_cap_w = float(solar_potential.get("panelCapacityWatts", 250))
    best = min(configs, key=lambda c: abs(c["panelsCount"] - panel_count))
    google_kwp = best["panelsCount"] * panel_cap_w / 1000
    if google_kwp <= 0:
        return _FALLBACK_SPECIFIC_YIELD
    return float(best["yearlyEnergyDcKwh"]) / google_kwp


def _south_facing_area(roof_segment_stats: list[dict]) -> float:
    """Sum area of segments facing south (azimuth 90–270°). Excludes N/NE/NW."""
    return sum(
        s.get("stats", {}).get("areaMeters2", 0)
        for s in roof_segment_stats
        if 90 <= s.get("azimuthDegrees", 0) <= 270
    )


def parse_roof(insights: dict, panel_area_m2: float = _DEFAULT_PANEL_AREA_M2) -> RoofData | None:
    """Parse raw buildingInsights response → RoofData. Returns None if no usable data."""
    sp = insights.get("solarPotential")
    if not sp:
        return None

    roof_segs = sp.get("roofSegmentStats", [])

    # Only count south-facing segments — N/NE/NW faces aren't viable
    usable_area = _south_facing_area(roof_segs)
    if usable_area <= 0:
        usable_area = float(sp.get("maxArrayAreaMeters2") or 0)
    if usable_area <= 0:
        return None

    max_modules = max(1, int(usable_area / panel_area_m2))
    orientation = _dominant_orientation(roof_segs)
    specific_yield = _specific_yield_from_configs(sp, max_modules)

    center = insights.get("center", {})
    return RoofData(
        max_modules=max_modules,
        usable_area_m2=usable_area,
        dominant_orientation=orientation,
        specific_yield_kwh_per_kwp=specific_yield,
        source="google_solar",
        lat=float(center.get("latitude", 0)),
        lng=float(center.get("longitude", 0)),
    )


def roof_from_address(
    address: str,
    *,
    geocoding_api_key: str | None = None,
    solar_api_key: str | None = None,
    panel_area_m2: float = _DEFAULT_PANEL_AREA_M2,
    floor_area_m2: float | None = None,
) -> RoofData:
    """
    Full pipeline: address string → geocode → Solar API → RoofData.

    Falls back to floor_area_m2 × 30% if Google Solar has no coverage.
    Raises GoogleSolarError if geocoding fails or fallback inputs missing.
    """
    geo_key = geocoding_api_key or os.environ.get("GOOGLE_GEOCODING_API_KEY", "")
    sol_key = solar_api_key or os.environ.get("GOOGLE_SOLAR_API_KEY", "")

    lat, lng = geocode(address, geo_key)

    try:
        insights = _fetch_building_insights(lat, lng, sol_key)
        roof = parse_roof(insights, panel_area_m2)
    except Exception:
        roof = None

    if roof is not None:
        return roof

    # Fallback — estimate from floor area
    if floor_area_m2 and floor_area_m2 > 0:
        usable = floor_area_m2 * _FALLBACK_USABLE_RATIO
        return RoofData(
            max_modules=max(1, int(usable / panel_area_m2)),
            usable_area_m2=usable,
            dominant_orientation="S",
            specific_yield_kwh_per_kwp=_FALLBACK_SPECIFIC_YIELD,
            source="floor_area_fallback",
            lat=lat,
            lng=lng,
        )

    raise GoogleSolarError(
        f"Google Solar has no coverage for {address!r} and no floor_area_m2 provided."
    )
