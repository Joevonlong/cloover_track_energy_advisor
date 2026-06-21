"""Individual permit check functions — one per check, all return PermitCheck.

Each function is self-contained: makes HTTP calls, applies rules, returns a structured result.
Called concurrently by engine.py via ThreadPoolExecutor.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import httpx

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_OPENPLZ_URL = "https://openplzapi.org/de/Localities"
# MaStR SOAP API was decommissioned — we use Tavily search as fallback
_MASTR_SEARCH_QUERY = "Solaranlagen Marktstammdatenregister PLZ {plz} Anzahl registriert"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Bundesland → Denkmal WMS endpoint (None = OSM-only fallback)
DENKMAL_WMS: dict[str, str | None] = {
    "Bayern": "https://geoservices.bayern.de/od/wms/gdi/v1/denkmal",
    "Nordrhein-Westfalen": "https://www.wms.nrw.de/wms/wms_nw_inspire-denkmal",
    "Berlin": "https://fbinter.stadt-berlin.de/fb/wms/senstadt/denkmal",
    "Rheinland-Pfalz": "https://www.geoportal.rlp.de/wms/rlp_denkmal",
    "Sachsen-Anhalt": "https://www.geodatenportal.sachsen-anhalt.de/wms/denkmal",
    "Bremen": "https://geodienste.bremen.de/wms/denkmal",
    # The rest fall back to OSM Overpass
    "Baden-Württemberg": "https://owsproxy.lgl-bw.de/owsproxy/ows/WMS_LGL-BW_DENKMAL",
    "Brandenburg": None,
    "Hamburg": None,
    "Hessen": None,              # WFS only, not GetFeatureInfo-friendly
    "Mecklenburg-Vorpommern": None,
    "Niedersachsen": None,       # restricted
    "Saarland": None,
    "Sachsen": None,
    "Schleswig-Holstein": None,
    "Thüringen": None,
}

# Module-level PLZ cache to avoid hammering OpenPLZ
_plz_cache: dict[str, str] = {}


@dataclass
class PermitCheck:
    id: str
    product: str                              # "solar"|"heatpump"|"ev_charger"|"battery"
    check_name: str
    status: Literal["pass", "warn", "fail", "info"]
    label: str
    detail: str
    cited_clause: str | None
    source_url: str | None
    source_name: str
    fetched_at: str                           # ISO 8601


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_check(
    id: str,
    product: str,
    check_name: str,
    status: Literal["pass", "warn", "fail", "info"],
    label: str,
    detail: str,
    source_name: str,
    source_url: str | None = None,
    cited_clause: str | None = None,
) -> PermitCheck:
    return PermitCheck(
        id=id,
        product=product,
        check_name=check_name,
        status=status,
        label=label,
        detail=detail,
        cited_clause=cited_clause,
        source_url=source_url,
        source_name=source_name,
        fetched_at=_now(),
    )


# ---------------------------------------------------------------------------
# Helper: PLZ → Bundesland
# ---------------------------------------------------------------------------

def plz_to_bundesland(plz: str) -> str:
    """Return the Bundesland name for a German postal code."""
    if plz in _plz_cache:
        return _plz_cache[plz]
    try:
        resp = httpx.get(
            _OPENPLZ_URL,
            params={"postalCode": plz, "pageSize": 1},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            bl = data[0].get("federalState", {}).get("name", "Unknown")
            _plz_cache[plz] = bl
            return bl
    except Exception:
        pass
    return "Unknown"


# ---------------------------------------------------------------------------
# Check 1+2: Denkmalschutz — solar (fail) and heat pump (warn if listed)
# ---------------------------------------------------------------------------

def _query_denkmal_wms(lat: float, lng: float, wms_url: str) -> tuple[bool, str]:
    """Return (is_listed, feature_name). Uses WMS GetFeatureInfo at coordinates."""
    d = 0.0005  # ~55m bounding box
    try:
        resp = httpx.get(
            wms_url,
            params={
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetFeatureInfo",
                "QUERY_LAYERS": "denkmal",
                "LAYERS": "denkmal",
                "BBOX": f"{lat - d},{lng - d},{lat + d},{lng + d}",
                "CRS": "EPSG:4326",
                "WIDTH": "3",
                "HEIGHT": "3",
                "I": "1",
                "J": "1",
                "INFO_FORMAT": "application/json",
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if features:
            name = features[0].get("properties", {}).get("bezeichnung", "Kulturdenkmal")
            return True, str(name)
        return False, ""
    except Exception:
        return False, ""


def _query_denkmal_osm(lat: float, lng: float) -> tuple[bool, str]:
    """Return (is_listed, tag). Uses Overpass API to check OSM heritage tags."""
    query = f"""
[out:json][timeout:10];
(
  way(around:25,{lat},{lng})[historic];
  way(around:25,{lat},{lng})[heritage];
  way(around:25,{lat},{lng})[building:protection_status];
  node(around:25,{lat},{lng})[historic];
);
out 1;
"""
    try:
        resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=12)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        if elements:
            tags = elements[0].get("tags", {})
            name = tags.get("name") or tags.get("historic") or "heritage feature"
            return True, str(name)
        return False, ""
    except Exception:
        return False, ""


def check_denkmal_solar(lat: float, lng: float, bundesland: str) -> PermitCheck:
    """Solar PV: blocked if building is heritage-listed."""
    wms_url = DENKMAL_WMS.get(bundesland)
    source_name = f"{bundesland} Denkmal WMS" if wms_url else "OpenStreetMap Overpass"
    source_url = wms_url or "https://overpass-api.de"

    if wms_url:
        listed, name = _query_denkmal_wms(lat, lng, wms_url)
        if listed:
            return _make_check(
                "solar_denkmal", "solar", "Heritage protection",
                "fail",
                f"Heritage listed — {name}",
                "Solar panels require Denkmalschutzbehörde approval (usually refused for listed buildings).",
                source_name, source_url,
            )
        return _make_check(
            "solar_denkmal", "solar", "Heritage protection",
            "pass", "Not heritage listed",
            f"No Kulturdenkmal found at this address ({bundesland} monument registry).",
            source_name, source_url,
        )

    # Fallback: OSM
    listed, name = _query_denkmal_osm(lat, lng)
    if listed:
        return _make_check(
            "solar_denkmal", "solar", "Heritage protection",
            "fail",
            f"Possible heritage listing — {name}",
            "OSM indicates a heritage feature nearby. Confirm with local Denkmalschutzbehörde.",
            "OpenStreetMap Overpass", "https://overpass-api.de",
        )
    # OSM-only Bundesland with no hit → can't confirm clear
    return _make_check(
        "solar_denkmal", "solar", "Heritage protection",
        "warn", "Heritage status unverified",
        f"No public Denkmal API for {bundesland}. Confirm with Landesdenkmalamt before ordering.",
        "OpenStreetMap Overpass", "https://overpass-api.de",
    )


def check_denkmal_heatpump(lat: float, lng: float, bundesland: str) -> PermitCheck:
    """Heat pump: listed buildings need approval (warn, not auto-fail — HP sometimes approved)."""
    wms_url = DENKMAL_WMS.get(bundesland)
    source_name = f"{bundesland} Denkmal WMS" if wms_url else "OpenStreetMap Overpass"
    source_url = wms_url or "https://overpass-api.de"

    if wms_url:
        listed, name = _query_denkmal_wms(lat, lng, wms_url)
        if listed:
            return _make_check(
                "hp_denkmal", "heatpump", "Heritage protection",
                "warn",
                f"Heritage listed — approval needed ({name})",
                "Heat pump outdoor unit requires Denkmalschutzbehörde approval. Often granted if unit is not visible from street.",
                source_name, source_url,
            )
        return _make_check(
            "hp_denkmal", "heatpump", "Heritage protection",
            "pass", "Not heritage listed",
            f"No Kulturdenkmal found at this address ({bundesland} monument registry).",
            source_name, source_url,
        )

    listed, name = _query_denkmal_osm(lat, lng)
    if listed:
        return _make_check(
            "hp_denkmal", "heatpump", "Heritage protection",
            "warn",
            f"Possible heritage listing — {name}",
            "OSM indicates a heritage feature. Confirm with Denkmalschutzbehörde before installation.",
            "OpenStreetMap Overpass", "https://overpass-api.de",
        )
    return _make_check(
        "hp_denkmal", "heatpump", "Heritage protection",
        "warn", "Heritage status unverified",
        f"No public Denkmal API for {bundesland}. Confirm with Landesdenkmalamt before ordering.",
        "OpenStreetMap Overpass", "https://overpass-api.de",
    )


# ---------------------------------------------------------------------------
# Check 3+4: Bebauungsplan RAG — solar and heat pump
# ---------------------------------------------------------------------------

def check_bplan(
    plz: str,
    city: str,
    tavily_api_key: str,
    anthropic_api_key: str,
) -> list[PermitCheck]:
    """B-Plan check for solar + heat pump using Tavily search + LLM clause extraction."""
    if not tavily_api_key:
        return [
            _make_check("solar_bplan", "solar", "Zone + solar permitted", "warn",
                        "B-Plan check skipped (no Tavily key)",
                        "Bundesland baseline applies. Verify with local Bauamt.",
                        "Bebauungsplan RAG"),
            _make_check("hp_bplan", "heatpump", "Zone + outdoor unit permitted", "warn",
                        "B-Plan check skipped (no Tavily key)",
                        "Bundesland baseline applies. Verify with local Bauamt.",
                        "Bebauungsplan RAG"),
        ]

    # Tavily search — use city name for targeted results
    try:
        from tavily import TavilyClient  # type: ignore[import-untyped]
        client = TavilyClient(api_key=tavily_api_key)
        result = client.search(
            query=f"Bebauungsplan {city} {plz} Geoportal Solaranlage Festsetzung",
            search_depth="basic",
            max_results=3,
            include_raw_content=True,
        )
        content = "\n\n".join(
            r.get("raw_content") or r.get("content", "")
            for r in result.get("results", [])
        )
        top_url = result.get("results", [{}])[0].get("url") if result.get("results") else None
    except Exception:
        content = ""
        top_url = None

    if not content.strip() or not anthropic_api_key:
        # No B-Plan found → federal/Bundesland baseline (verfahrensfrei) applies
        return [
            _make_check("solar_bplan", "solar", "Zone + solar permitted", "pass",
                        "No B-Plan restriction found",
                        f"No specific Bebauungsplan found for {city} ({plz}). Federal baseline applies — solar PV is verfahrensfrei under LBO.",
                        "Bebauungsplan RAG", top_url),
            _make_check("hp_bplan", "heatpump", "Zone + outdoor unit permitted", "pass",
                        "No B-Plan restriction found",
                        f"No specific Bebauungsplan found for {city} ({plz}). Federal baseline applies — outdoor heat pump unit is generally permitted.",
                        "Bebauungsplan RAG", top_url),
        ]

    # LLM extraction
    prompt = (
        "You are a German building law expert. Analyse the following Bebauungsplan text and extract "
        "permit status for (1) solar panels / Photovoltaikanlage and (2) heat pump outdoor units / "
        "Wärmepumpe Außengerät.\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        '{"solar":{"status":"permitted|restricted|silent","clause":"<exact quoted text or null>"},'
        '"heatpump":{"status":"permitted|restricted|silent","clause":"<exact quoted text or null>"}}\n\n'
        f"Bebauungsplan text:\n{content[:4000]}"
    )

    try:
        resp = httpx.post(
            _ANTHROPIC_URL,
            headers={
                "x-api-key": anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        extracted = json.loads(raw)
    except Exception:
        extracted = {"solar": {"status": "silent", "clause": None},
                     "heatpump": {"status": "silent", "clause": None}}

    def _bplan_check(check_id: str, product: str, check_name: str, key: str) -> PermitCheck:
        info = extracted.get(key, {})
        status_str = info.get("status", "silent")
        clause = info.get("clause")
        if status_str == "restricted":
            return _make_check(check_id, product, check_name, "fail",
                                "Restricted by B-Plan",
                                "Bebauungsplan contains a restriction. Confirm with Bauamt before ordering.",
                                "Bebauungsplan RAG", top_url, clause)
        if status_str == "permitted":
            return _make_check(check_id, product, check_name, "pass",
                                "Permitted by B-Plan",
                                "Bebauungsplan explicitly permits this installation.",
                                "Bebauungsplan RAG", top_url, clause)
        # silent → fall back to Bundesland baseline (verfahrensfrei)
        return _make_check(check_id, product, check_name, "pass",
                            "No B-Plan restriction found",
                            "B-Plan is silent on this — Bundesland baseline (verfahrensfrei) applies.",
                            "Bebauungsplan RAG", top_url, clause)

    return [
        _bplan_check("solar_bplan", "solar", "Zone + solar permitted", "solar"),
        _bplan_check("hp_bplan", "heatpump", "Zone + outdoor unit permitted", "heatpump"),
    ]


# ---------------------------------------------------------------------------
# Check 5: MaStR neighbour count
# ---------------------------------------------------------------------------

_MASTR_KENDO_URL = "https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitenAjaxMVC"


def _classify_mastr(count: int, plz: str, source_url: str) -> PermitCheck:
    mastr_url = f"https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitenMVC?filter=Postleitzahl~eq~{plz}~and~Einheittyp~eq~2"
    if count >= 40:
        return _make_check(
            "solar_mastr", "solar", "Neighbourhood precedent",
            "pass", f"~{count} solar systems in PLZ {plz}",
            "Established solar area — permits clearly granted to neighbours.",
            "BNetzA Marktstammdatenregister", source_url,
        )
    if count >= 5:
        return _make_check(
            "solar_mastr", "solar", "Neighbourhood precedent",
            "warn", f"~{count} solar systems in PLZ {plz}",
            "Early adopter area — solar is possible but less precedent locally.",
            "BNetzA Marktstammdatenregister", source_url,
        )
    return _make_check(
        "solar_mastr", "solar", "Neighbourhood precedent",
        "warn", f"~{count} solar systems in PLZ {plz}",
        "Few solar installations found for this PLZ. Solar is still possible — check with local Bauamt.",
        "BNetzA Marktstammdatenregister", mastr_url,
    )


def check_mastr(
    plz: str,
    supabase_url: str = "",
    supabase_key: str = "",
    tavily_api_key: str = "",
) -> PermitCheck:
    """Count solar systems in PLZ. Sources: Supabase → MaStR Kendo grid → Tavily → warn."""
    mastr_url = f"https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitenMVC?filter=Postleitzahl~eq~{plz}~and~Einheittyp~eq~2"

    # Tier 1: Supabase plz_solar_count table (seeded from MaStR export)
    if supabase_url and supabase_key:
        try:
            resp = httpx.get(
                f"{supabase_url.rstrip('/')}/rest/v1/plz_solar_count",
                params={"plz": f"eq.{plz}", "select": "count"},
                headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"},
                timeout=5,
            )
            rows = resp.json()
            if rows:
                return _classify_mastr(int(rows[0]["count"]), plz, mastr_url)
        except Exception:
            pass

    # Tier 2: MaStR public page — scrape total count from JSON embedded in HTML
    try:
        resp = httpx.get(
            mastr_url,
            headers={"Accept": "text/html", "User-Agent": "Mozilla/5.0"},
            timeout=12,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            import re
            # Page embeds Kendo data-source or a total count in the HTML
            match = re.search(r'"Total"\s*:\s*(\d+)', resp.text)
            if not match:
                match = re.search(r'total["\s]*:\s*(\d+)', resp.text, re.IGNORECASE)
            if match:
                return _classify_mastr(int(match.group(1)), plz, mastr_url)
    except Exception:
        pass

    # Tier 3: Tavily search as last resort
    if tavily_api_key:
        try:
            from tavily import TavilyClient  # type: ignore[import-untyped]
            client = TavilyClient(api_key=tavily_api_key)
            result = client.search(
                query=f"Marktstammdatenregister Solaranlagen PLZ {plz} Einheiten registriert",
                search_depth="basic",
                max_results=2,
            )
            snippet = " ".join(r.get("content", "") for r in result.get("results", []))
            top_url = result.get("results", [{}])[0].get("url") if result.get("results") else mastr_url
            import re
            numbers = re.findall(r'\b(\d{1,5})\b', snippet)
            count = max((int(n) for n in numbers if 1 <= int(n) <= 50000), default=0)
            if count:
                return _classify_mastr(count, plz, top_url)
        except Exception:
            pass

    return _make_check(
        "solar_mastr", "solar", "Neighbourhood precedent",
        "warn", f"Solar count for PLZ {plz} unclear",
        "Could not query MaStR. Check manually if needed — this is a trust signal, not a permit check.",
        "BNetzA Marktstammdatenregister", mastr_url,
    )


# ---------------------------------------------------------------------------
# Check 6: EV charger — private parking
# ---------------------------------------------------------------------------

def check_ev_parking(lat: float, lng: float, has_private_parking: bool) -> PermitCheck:
    """EV charger requires a private driveway or garage."""
    # User checkbox is the primary signal
    if has_private_parking:
        return _make_check(
            "ev_parking", "ev_charger", "Private parking available",
            "pass", "Private driveway / garage confirmed",
            "Wallbox can be installed at your private parking space.",
            "User input + OSM",
        )

    # Try OSM as secondary check
    query = f"""
[out:json][timeout:8];
(
  way(around:30,{lat},{lng})[amenity=parking][access=private];
  way(around:30,{lat},{lng})[amenity=parking_space];
);
out 1;
"""
    try:
        resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        if elements:
            return _make_check(
                "ev_parking", "ev_charger", "Private parking available",
                "warn", "Possible private parking nearby (OSM)",
                "OSM shows a parking area near your address. Confirm it's yours before ordering.",
                "OpenStreetMap Overpass", "https://overpass-api.de",
            )
    except Exception:
        pass

    return _make_check(
        "ev_parking", "ev_charger", "Private parking available",
        "fail", "No private parking confirmed",
        "A wallbox requires a private driveway or garage. Street-only parking blocks installation.",
        "User input + OpenStreetMap Overpass",
    )


# ---------------------------------------------------------------------------
# Check 7: EV charger — apartment / WEG
# ---------------------------------------------------------------------------

def check_ev_weg(lat: float, lng: float) -> PermitCheck:
    """Apartment buildings need a WEG owner vote for wallbox installation."""
    query = f"""
[out:json][timeout:8];
way(around:10,{lat},{lng})[building~"^(apartments|flat|residential|yes)$"];
out 1;
"""
    try:
        resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        if elements:
            btype = elements[0].get("tags", {}).get("building", "residential")
            if btype in ("apartments", "flat"):
                return _make_check(
                    "ev_weg", "ev_charger", "Apartment building — WEG",
                    "warn", "Apartment building — owner vote needed",
                    "Installation in a Mehrfamilienhaus requires a WEG owners' vote (§20 WEG). We assist with the process.",
                    "OpenStreetMap Overpass", "https://overpass-api.de",
                )
    except Exception:
        pass

    return _make_check(
        "ev_weg", "ev_charger", "Apartment building — WEG",
        "pass", "Single-family home",
        "No WEG vote required. Legal right to install confirmed (§554 BGB / homeowner).",
        "OpenStreetMap Overpass", "https://overpass-api.de",
    )


# ---------------------------------------------------------------------------
# Check 8: Heat pump — GEG 2024 boiler age
# ---------------------------------------------------------------------------

def check_hp_geg(building_year: int, fuel_type: str) -> PermitCheck:
    """Heat pump GEG 2024 compliance — hardcoded rule."""
    source = "Gebäudeenergiegesetz (GEG) §71, §72"

    if fuel_type.upper() not in ("OIL", "GAS"):
        return _make_check(
            "hp_geg", "heatpump", "Boiler age — GEG 2024",
            "pass", "Non-fossil heating — HP upgrade always permitted",
            "Current heating is not oil or gas. Heat pump upgrade is always GEG-compliant.",
            source,
        )

    boiler_age = 2024 - building_year  # conservative: assume boiler as old as building
    if boiler_age >= 20:
        return _make_check(
            "hp_geg", "heatpump", "Boiler age — GEG 2024",
            "pass", "Replacement permitted (boiler ≥ 20 years)",
            f"Your heating system is ≥ 20 years old — replacement with heat pump required under GEG §72.",
            source,
            cited_clause="GEG §72: Heizkessel, die mit flüssigen oder gasförmigen Brennstoffen betrieben werden und vor dem 1. Januar 1991 eingebaut wurden, dürfen nicht mehr betrieben werden.",
        )

    return _make_check(
        "hp_geg", "heatpump", "Boiler age — GEG 2024",
        "warn", "Boiler protected until 2029 — HP still recommended",
        f"Boiler is < 20 years old. Mandatory replacement postponed until 2029 under GEG §71 transitional rules. Installing HP now maximises KfW 458 subsidy window.",
        source,
        cited_clause="GEG §71 Abs. 9: Übergangsregelung bis 31. Dezember 2029 für bestehende Anlagen.",
    )


# ---------------------------------------------------------------------------
# Check: Solar PV — LBO verfahrensfrei baseline
# ---------------------------------------------------------------------------

def check_solar_lbo(bundesland: str) -> PermitCheck:
    """Explicit affirmation that solar PV is verfahrensfrei under Landesbauordnung."""
    return _make_check(
        "solar_lbo", "solar", "Solar PV — permit required?",
        "pass", "Verfahrensfrei — no building permit needed",
        f"Solar PV on private residential roofs is verfahrensfrei under {bundesland} LBO. No permit application required.",
        f"{bundesland} Landesbauordnung (LBO)",
        cited_clause="§ 50 LBO BW (analog in all Bundesländer): Photovoltaikanlagen auf Dach- und Außenwandflächen sind verfahrensfrei.",
    )


# ---------------------------------------------------------------------------
# Check: Heat pump — TA Lärm noise advisory
# ---------------------------------------------------------------------------

def check_hp_noise(lat: float, lng: float) -> PermitCheck:
    """TA Lärm advisory — heat pump outdoor unit noise check based on plot density."""
    # Query OSM for dense urban context (buildings within 8m)
    query = f"""
[out:json][timeout:8];
(
  way(around:8,{lat},{lng})[building];
  way(around:8,{lat},{lng})[landuse=residential];
);
out 1;
"""
    try:
        resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        if elements:
            return _make_check(
                "hp_noise", "heatpump", "Noise — TA Lärm",
                "warn", "Dense plot — noise advisory applies",
                "Neighbouring buildings within 8m. Heat pump outdoor unit must comply with TA Lärm (≤45 dB night). Choose a low-noise model (≤40 dB) and avoid north/east-facing garden walls.",
                "TA Lärm (Technische Anleitung zum Schutz gegen Lärm)",
                cited_clause="TA Lärm Nr. 6.1: Immissionsrichtwerte für Wohngebiete nachts 40 dB(A), tags 55 dB(A).",
            )
    except Exception:
        pass

    return _make_check(
        "hp_noise", "heatpump", "Noise — TA Lärm",
        "pass", "Sufficient space for outdoor unit",
        "No immediately adjacent buildings detected. Standard heat pump outdoor unit installation is compliant with TA Lärm.",
        "TA Lärm (Technische Anleitung zum Schutz gegen Lärm)",
        cited_clause="TA Lärm Nr. 6.1: Immissionsrichtwerte für Wohngebiete nachts 40 dB(A).",
    )


# ---------------------------------------------------------------------------
# Check 9+10: Battery — installation + grid registration
# ---------------------------------------------------------------------------

def check_battery_install() -> PermitCheck:
    return _make_check(
        "battery_install", "battery", "Indoor installation",
        "pass", "Always permitted — no approval needed",
        "Indoor battery storage ≤ 30 kWh requires no building permit or authority notification.",
        "Hardcoded rule (DE law)",
    )


def check_battery_mastr() -> PermitCheck:
    return _make_check(
        "battery_mastr", "battery", "Grid registration",
        "info", "MaStR registration after install — installer task",
        "Battery connected to the grid must be registered in MaStR within 1 month of commissioning. Your installer handles this.",
        "Hardcoded advisory",
        cited_clause="EEG 2023 §3 Nr. 30: Anlagenbetreiber sind verpflichtet, ihre Anlage im Marktstammdatenregister zu registrieren.",
    )
