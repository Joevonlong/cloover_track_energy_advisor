# Permit Layer — How It Works

## Overview

Step 2 in the user journey. Fires in parallel with the solar engine the moment an address is confirmed.

**Core question:** Can this specific building legally install solar / heat pump / EV charger / battery?

Five data sources cover all **12 checks**:
- **Bebauungsplan RAG** (Tavily search + Claude Haiku) → Solar PV + Heat pump
- **Denkmal WMS** (per-Bundesland endpoints, OSM Overpass fallback) → Solar PV + Heat pump
- **MaStR neighbour count** (Supabase → public page scrape → Tavily) → Solar PV trust signal
- **OSM Overpass** → EV parking, WEG building type, heat-pump noise density
- **Hardcoded rules** → Solar LBO baseline, Heat pump GEG, Heat pump TA Lärm, Battery

If any check returns `fail` for a product → that product is flagged blocked (`solar_blocked`,
`heatpump_blocked`, `ev_charger_blocked`) and removed from all savings offers. No phantom savings.

---

## The 12 Checks

| # | Product | Check (id) | Source | Possible results |
|---|---|---|---|---|
| 1 | Solar PV | Permit required? (`solar_lbo`) | Landesbauordnung (hardcoded) | ✅ verfahrensfrei |
| 2 | Solar PV | Heritage protection (`solar_denkmal`) | Denkmal WMS / OSM | ✅ not listed / 🟡 unverified / 🔴 listed — blocked |
| 3 | Solar PV | Zone + solar permitted (`solar_bplan`) | Bebauungsplan RAG | ✅ permitted/silent / 🟡 skipped / 🔴 restricted |
| 4 | Solar PV | Neighbourhood precedent (`solar_mastr`) | MaStR count | ✅ ≥40 / 🟡 <40 or unclear |
| 5 | Heat pump | Heritage protection (`hp_denkmal`) | Denkmal WMS / OSM | ✅ not listed / 🟡 listed — approval needed |
| 6 | Heat pump | Zone + outdoor unit (`hp_bplan`) | Bebauungsplan RAG | ✅ permitted/silent / 🟡 skipped / 🔴 restricted |
| 7 | Heat pump | Boiler age — GEG 2024 (`hp_geg`) | Hardcoded rule | ✅ replacement permitted / 🟡 protected until 2029 |
| 8 | Heat pump | Noise — TA Lärm (`hp_noise`) | OSM density + hardcoded | ✅ space OK / 🟡 dense plot advisory |
| 9 | EV Charger | Private parking (`ev_parking`) | User input + OSM | ✅ confirmed / 🟡 OSM maybe / 🔴 none — blocked |
| 10 | EV Charger | Apartment — WEG (`ev_weg`) | OSM building type | ✅ single family / 🟡 apartment — owner vote |
| 11 | Battery | Indoor installation (`battery_install`) | Hardcoded rule | ✅ always permitted |
| 12 | Battery | Grid registration (`battery_mastr`) | Hardcoded advisory | ℹ️ register in MaStR — installer task |

Status vocabulary is `pass` / `warn` / `fail` / `info` (rendered as ✅ / 🟡 / 🔴 / ℹ️).
Only `fail` blocks a product. `check_bplan` returns **two** checks (`solar_bplan` + `hp_bplan`);
every other function returns one — 11 functions → 12 checks.

Every result carries:
- The **source URL** queried (`source_url`)
- The **source name** (`source_name`)
- The **timestamp** it was fetched (`fetched_at`, ISO 8601 UTC)
- The **exact clause** or feature name that triggered the result (`cited_clause`)

---

## Entry points

**Library:** `run_permit_checks()` in `engine.py`

```python
from app.domain.savings.permit_layer import run_permit_checks

matrix = run_permit_checks(
    address="Am Nahholz 55, 74722 Buchen",
    plz="74722",
    lat=49.52, lng=9.32,
    intake={"building_year": 1985, "fuel_type": "GAS", "has_private_parking": True},
    tavily_api_key=...,      # optional — B-Plan + MaStR fallback
    anthropic_api_key=...,   # optional — B-Plan clause extraction + German summary
    supabase_url=..., supabase_key=...,  # optional — cache + plz_solar_count
)  # → PermitMatrix
```

**API:** `routes/permits.py`
- `POST /api/v1/advisor/permits` → full `PermitMatrix` JSON (batch)
- `GET  /api/v1/advisor/permits/stream` → SSE, **one event per check as it resolves**
  (this is what drives the live tick-by-tick UI in Step 2)

**Concurrency:** all checks run on a `ThreadPoolExecutor(max_workers=6)` with synchronous
`httpx` calls, collected via `as_completed`. No `asyncio`. Each task is wrapped in `_safe()`
so a single failing check degrades to a `warn` ("Check unavailable") instead of crashing the matrix.

---

## Data Source 1 — Bebauungsplan RAG  (`check_bplan`)

### What it is
A Bebauungsplan (B-Plan) is a legally binding local development plan set by the Gemeinde.
It can restrict solar panels (e.g. prohibit reflective surfaces) or outdoor heat-pump units.
The restrictions are written in German legal text, usually inside a PDF.

### How we read it (Tavily search + LLM, not vector embeddings)
Germany has no single national B-Plan API, so we retrieve loosely and let the LLM extract:

```
city + plz
  → Tavily search: "Bebauungsplan {city} {plz} Geoportal Solaranlage Festsetzung"
    (search_depth=basic, max_results=3, include_raw_content=True)
  → concatenate raw_content of top results
  → Claude Haiku (claude-haiku-4-5) extracts strict JSON:
      {"solar":   {"status":"permitted|restricted|silent","clause": "<quoted text|null>"},
       "heatpump":{"status":"permitted|restricted|silent","clause": "<quoted text|null>"}}
  → map status → permit result (see below)
```

### Status mapping
- `restricted` → **fail** ("Restricted by B-Plan", clause quoted)
- `permitted`  → **pass** ("Permitted by B-Plan")
- `silent` / nothing found → **pass** ("No B-Plan restriction found" — Bundesland baseline / verfahrensfrei applies)
- no Tavily key → **warn** ("B-Plan check skipped (no Tavily key)")

The `top_url` from Tavily is attached as `source_url` so the user can open the source.

---

## Data Source 2 — Denkmal WMS  (`check_denkmal_solar`, `check_denkmal_heatpump`)

### Why address-level matters
Denkmalschutz is the biggest permit killer. A heritage-listed building (or its street ensemble)
requires Denkmalschutzbehörde approval for *any* exterior change — and approval for solar is
usually refused. Must be checked at the exact building coordinates, not at PLZ or Bundesland level.

### Endpoint map (`DENKMAL_WMS` in `checks.py`)

| Bundesland | WMS endpoint |
|---|---|
| Bayern | `geoservices.bayern.de/od/wms/gdi/v1/denkmal` |
| Nordrhein-Westfalen | `wms.nrw.de/wms/wms_nw_inspire-denkmal` |
| Berlin | `fbinter.stadt-berlin.de/fb/wms/senstadt/denkmal` |
| Rheinland-Pfalz | `geoportal.rlp.de/wms/rlp_denkmal` |
| Sachsen-Anhalt | `geodatenportal.sachsen-anhalt.de/wms/denkmal` |
| Bremen | `geodienste.bremen.de/wms/denkmal` |
| Baden-Württemberg | `owsproxy.lgl-bw.de/owsproxy/ows/WMS_LGL-BW_DENKMAL` |
| All others | `None` → OSM Overpass fallback |

### Query logic
```
1. plz_to_bundesland(plz)            via OpenPLZ API (openplzapi.org), module-cached
2. if Bundesland has a WMS:
     WMS GetFeatureInfo at (lat,lng), ~55m bbox (d=0.0005°), INFO_FORMAT=application/json
       hit  → read feature name (properties.bezeichnung)
3. else (OSM-only Bundesland):
     Overpass around:25m for [historic] / [heritage] / [building:protection_status]
```

### Result semantics (Solar vs Heat pump differ)
| Situation | Solar (`solar_denkmal`) | Heat pump (`hp_denkmal`) |
|---|---|---|
| WMS hit (listed) | 🔴 **fail** — solar usually refused | 🟡 **warn** — approval needed, often granted if unit hidden |
| WMS, no hit | ✅ **pass** — not listed | ✅ **pass** — not listed |
| OSM fallback hit | 🔴 **fail** — confirm with Behörde | 🟡 **warn** — confirm with Behörde |
| OSM fallback, no hit | 🟡 **warn** — status unverified (no public API) | 🟡 **warn** — status unverified |

**Conservative rule:** a clean ✅ is only emitted when a real state WMS returned nothing.
OSM-only Bundesländer can never confirm "clear" → 🟡 "confirm with Landesdenkmalamt".

---

## Data Source 3 — MaStR neighbour count  (`check_mastr`)

**Not a permit check — a trust signal.** Shows the homeowner that neighbours already did it.
The historic MaStR SOAP API was decommissioned, so we use a 3-tier fallback:

```
Tier 1  Supabase  plz_solar_count  (seeded offline from a MaStR export — fast, no rate limit)
Tier 2  MaStR public Kendo page    marktstammdatenregister.de/.../EinheitenMVC?filter=Postleitzahl~eq~{plz}~and~Einheittyp~eq~2
                                    → regex the embedded "Total": <n> count out of the HTML
Tier 3  Tavily search              "Marktstammdatenregister Solaranlagen PLZ {plz} ..." → parse a plausible number
        else → warn "count unclear"
```

| Count | Status | Meaning |
|---|---|---|
| ≥ 40 | ✅ pass | Established solar area — permits clearly granted to neighbours |
| 5–39 | 🟡 warn | Early-adopter area |
| 0–4  | 🟡 warn | Few installations — solar still possible, check local Bauamt |

Note: a low count is **never** a `fail`. It is informational only — the `solar_mastr` check
cannot block solar. `neighbour_count` on the matrix is parsed from this check's label when it passes.

---

## Data Source 4 — OSM Overpass

Used by three checks, all against the building coordinates.

**EV parking (`check_ev_parking`)** — user checkbox is the primary signal:
```
has_private_parking == True  → ✅ pass (wallbox location confirmed)
else Overpass around:30m [amenity=parking][access=private] / [amenity=parking_space]
       hit → 🟡 warn "possible private parking nearby — confirm it's yours"
       none → 🔴 fail "no private parking — street-only blocks installation"
```

**WEG building type (`check_ev_weg`)**:
```
Overpass around:10m building ~ ^(apartments|flat|residential|yes)$
  apartments|flat → 🟡 warn "Mehrfamilienhaus — WEG owner vote needed (§20 WEG)"
  else            → ✅ pass "single-family — legal right to install (§554 BGB)"
```

**Heat-pump noise (`check_hp_noise`)** — TA Lärm advisory by plot density:
```
Overpass around:8m [building] / [landuse=residential]
  adjacent buildings → 🟡 warn "dense plot — TA Lärm ≤45 dB night, pick low-noise model"
  none               → ✅ pass "sufficient space for outdoor unit"
```

---

## Hardcoded Rules

**Solar PV — LBO verfahrensfrei (`check_solar_lbo`):** always ✅ pass.
Cites `§ 50 LBO BW (analog in all Bundesländer): Photovoltaikanlagen … sind verfahrensfrei.`

**Boiler age — GEG 2024 (`check_hp_geg`):**
```python
if fuel_type.upper() not in ("OIL", "GAS"):
    status = "pass"   # non-fossil heating → HP upgrade always GEG-compliant
else:
    boiler_age = 2024 - building_year     # conservative: boiler assumed as old as building
    if boiler_age >= 20:
        status = "pass"   # ≥20y → replacement required under GEG §72
    else:
        status = "warn"   # <20y → protected until 2029 (GEG §71), HP still recommended
```
Source: `Gebäudeenergiegesetz (GEG) §71, §72`.

**Battery — indoor install (`check_battery_install`):** always ✅ pass.
`Indoor battery storage ≤ 30 kWh requires no building permit or notification.`

**Battery — grid registration (`check_battery_mastr`):** always ℹ️ info.
`EEG 2023 §3 Nr. 30` — register in MaStR within 1 month of commissioning (installer task).

---

## Output structures (`checks.py`, `engine.py`)

```python
@dataclass
class PermitCheck:
    id: str                            # e.g. "solar_denkmal" (see check IDs)
    product: str                       # "solar" | "heatpump" | "ev_charger" | "battery"
    check_name: str                    # display name
    status: Literal["pass","warn","fail","info"]
    label: str                         # one-line UI text
    detail: str                        # explanation sentence
    cited_clause: str | None           # exact quoted text (B-Plan / law)
    source_url: str | None             # link shown to user
    source_name: str                   # e.g. "Bayern Denkmal WMS"
    fetched_at: str                    # ISO 8601 UTC

@dataclass
class PermitMatrix:
    address: str
    lat: float
    lng: float
    plz: str
    bundesland: str
    checks: list[PermitCheck]          # 12 checks
    any_fatal: bool                    # True if any product is blocked
    solar_blocked: bool                # any solar check == "fail"
    heatpump_blocked: bool             # any heatpump check == "fail"
    ev_charger_blocked: bool           # any ev_charger check == "fail"
    neighbour_count: int               # parsed from solar_mastr when it passes
    summary_de: str                    # 2–3 sentence German summary (Claude Haiku)
```

Check IDs: `solar_lbo`, `solar_denkmal`, `solar_bplan`, `solar_mastr`, `hp_denkmal`,
`hp_bplan`, `hp_geg`, `hp_noise`, `ev_parking`, `ev_weg`, `battery_install`, `battery_mastr`.

`summary_de` is generated by Claude Haiku (`claude-haiku-4-5`) from the check labels — a short,
factual German paragraph stating what is permitted, what needs checking, and what is impossible.
Empty string if no Anthropic key is configured.

---

## Caching

Whole matrices are cached in Supabase `permit_cache`, keyed by `address_hash`
(`sha256(address.lower().strip())[:32]`), TTL **7 days**.
- `_load_cache` rehydrates a `PermitMatrix` from `result_json` if `fetched_at` is < 7 days old.
- `_save_cache` upserts with `Prefer: resolution=merge-duplicates`; write failures are non-fatal.
- No Supabase keys → checks always run live.

---

## Files

| File | Purpose |
|---|---|
| `INFO.md` | This file |
| `checks.py` | All 11 check functions + `PermitCheck`, `plz_to_bundesland`, `DENKMAL_WMS` map, OSM/WMS helpers |
| `engine.py` | `run_permit_checks()` → ThreadPool fan-out → flatten → blocked flags → `summary_de` → `PermitMatrix`; Supabase cache |
| `__init__.py` | Exports `PermitCheck`, `PermitMatrix`, `run_permit_checks`, `plz_to_bundesland` |

The SSE/batch HTTP surface lives one level up in `app/api/routes/permits.py`.
