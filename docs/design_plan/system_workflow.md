# System Workflow — Heimwende Energy Advisor (Cloover track)

> **Status:** optimised, source-verified, feedback-applied · **v0.3.1** · 2026-06-20
> **Source of truth:** [`specs/`](../../specs/) wins over this doc. This file is the *executable
> blueprint* tying the [master plan](./heimwende-master-plan.md), the [domain spec](../../specs/domain/savings-engine.spec.md)
> and the frozen [`openapi.yaml`](../../specs/api/openapi.yaml) into one pipeline, with every data
> source, price and formula pinned to an **official source** and a fallback.
> **North Star:** `monthly_saving = current_monthly_spend − (loan_installment + new_energy_cost)`.
>
> **The comparison core is four stacked upgrade layers** (this is the spine of the whole document):
>
> ```
>  Layer 1: + Solar / PV   →   Layer 2: + Battery   →   Layer 3: + Heat pump   →   Layer 4: + EV charger
> ```
>
> The user adds them **one at a time, Check24-style**; each click recomputes the single monthly number
> and shows what *that* layer adds. Everything below is organised around these four layers.

---

## 0. What changed

### Round 2 (v0.3.1 — this pass): upgrade-condition edge cases

The four layers each now cover the *realistic* household states, not just the clean fossil case:

- **Layer 4 (EV charger) now also serves "already drives an EV but has no home charger"** (§3.2, §5.4,
  §6.3). A wallbox lets them charge cheap at home (PV surplus / off-peak dynamic tariff) instead of
  expensive public charging — the saving is the *charging-cost* swap, not a vehicle swap.
- **Layer 3 (Heat pump) now also serves "already has an old/inefficient heat pump"** (§3.2, §5.3,
  §6.3). The offer becomes an **efficiency upgrade** to a state-of-the-art high-SCOP unit; the saving
  is the lower running cost (old SCOP → new SCOP). Note the **KfW eligibility nuance**: HP→HP
  replacement does *not* earn the Klima-Geschwindigkeitsbonus (that needs a fossil/old system), so the
  modelled grant is lower than a fossil→HP swap.
- **§6.3 dependency/toggle rules updated** so each layer is offered in exactly the right states, and
  the whole plan was re-checked for consistency with these conditions.

### Round 1 (v0.3): applied directly from `feedback_plan.md`

1. **Intake hardened** (§3): street **+ house number is now mandatory**; added **floor area** and
   **building year**; mobility is now **km-based** (€ → km conversion, then all maths use km); added an
   **"already has solar/battery"** path that is counted and folded into the ladder.
2. **The four layers are unified** as `+Solar → +Battery → +Heat pump → +EV` and renumbered Layer 1–4
   throughout. The old "Layer 1 = permits" is now a **pre-step (Site-Check)**, not a numbered layer.
3. **All financial / policy / price data now cites an official source** (Bundesnetzagentur, KfW,
   SMARD, GEG, Destatis, BAFA) — see §10–§12.
4. **The battery "−€20/mo" was wrong and is re-derived transparently** (§8.1): under the corrected
   load-aware self-consumption model it is **≈ €0/mo** at the battery rung, and the doc now shows the
   full sub-calculation and explains *why*.
5. **Reference dataset now has a "used in" column** (§10) — exactly which layer/step consumes each
   constant, so it is clear nothing is dead weight.
6. **Data sources are explained and mapped** to the layer/step they feed (§11).
7. **Two resource lists added** (§13): (1) a comprehensive list of everything available, and (2) the
   optimal minimal list for our current design.
8. **Product unit prices are no longer hard-coded** — they live in a **`price_catalog` table in
   Supabase** read at request time (§12); the domain stays pure (prices are injected, not imported).
9. **Savings certainty is now a first-class section** (§7) covering local irradiance, the **dynamic
   tariff** (emphasised — SMARD/EPEX day-ahead), applicable subsidies, and the self-consumption ratio.

Earlier (v0.2) fixes retained: corrected EV distance formula; EEG feed-in **7.78 ct/kWh**; nationally
correct permit model; GEG/WEG legalities; arbitrage = `spread × cycles × round-trip`; PVGIS primary /
Google Solar optional; Vite + FastAPI + Supabase stack with no secrets in the bundle.

---

## 1. Tech stack & how it shapes the architecture

| Layer | Choice | Notes |
|-------|--------|-------|
| Frontend | **Vite + React + TS + Tailwind** (SPA) | RHF + Zod intake; TanStack Query; the configurator (§6) is local state. |
| Backend | **FastAPI** (Python 3.12, `uv`) | Owns the pure domain core **and** is the BFF. |
| Data | **Supabase (Postgres)** | Reference dataset, **`price_catalog`**, response cache, persisted runs + proposals, optional installer auth. |
| LLM | Provider-agnostic adapter, **Claude default** | Explains/sells; **never computes** the number. |
| Contract | `specs/api/openapi.yaml` → generated TS client | FE codes against the client; BE implements the schema. |

**Vite removes the Next.js server tier — FastAPI is the only server and *is* the BFF.**

- Every third-party call (PVGIS, SMARD/aWATTar, Google Solar, Anthropic) is **server-side**. The SPA
  only ever calls FastAPI.
- **No secret in the frontend.** Vite inlines every `VITE_*` var into the public bundle, so the **only**
  frontend var is `VITE_API_BASE_URL`. All keys live in FastAPI's env.
- **CORS** allows the Vite dev origin (`http://localhost:5173`) + the deployed origin only.
- **Demo determinism:** a `?fixture=<id>` path on `/recommend` returns a frozen payload.

```
  Vite SPA  ──HTTPS──▶  FastAPI  ──▶  domain core (pure, TDD, zero I/O) — Layers 1–4
 (no secrets)            (BFF)    └─▶  adapters ─▶ PVGIS · SMARD/aWATTar · Google Solar · Anthropic
                           └────────▶  Supabase (cache · reference data · price_catalog · runs)
```

---

## 2. End-to-end pipeline

```
 PRE-STEPS                                CORE: four stacked layers              OUTPUT
 ┌────────┐  ┌────────────┐  ┌─────────┐  ┌───────────────────────────────┐  ┌──────────┐  ┌────────┐
 │ INTAKE │─▶│ SITE-CHECK │─▶│ RESOLVER│─▶│ L1 +Solar ▸ L2 +Battery ▸     │─▶│ OPTIMISER│─▶│ ADVISOR│
 │form/LLM│  │ permits §4 │  │ enrich  │  │ L3 +Heat pump ▸ L4 +EV charger │  │ max net  │  │ LLM    │
 └────────┘  └────────────┘  │ §10-12  │  │ (pure engine, on running state)│  └──────────┘  │ proposal│
                             └─────────┘  └───────────────────────────────┘                 └────────┘
```

The four layers + optimiser are the **pure domain core** (deterministic, unit-tested). Intake,
Site-Check and Resolver are **adapters** (I/O, cached). The Advisor is the **LLM adapter** (formats,
never computes).

---

## 3. Intake — inputs (updated)

### 3.1 Mandatory inputs

| Field | Type | Mandatory | Drives |
|---|---|:--:|---|
| **Address: street + house number** | string | ✅ **yes** | Site-Check (permits), roof geometry (Google Solar), precise lat/lon |
| Postcode (PLZ) | 5-digit | ✅ | irradiance, grid fee, climate, prices |
| City | string | ✅ | address completion |
| **Floor area** `floor_area_m2` | int | ✅ | heat-load (Layer 3), roof-size sanity |
| **Building year** `building_year` | int | ✅ | heat-load factor (Layer 3) |
| Occupants | int | ✅ | load profile / consumption scaling |
| Electricity spend | €/mo | ✅ | electricity baseline (Layer 1/2) |
| Heating `{fuel, eur_month}` | enum + € | ✅ | heating baseline + Layer 3 upside |
| **Mobility `{kind, km_month \| eur_month}`** | enum + km/€ | ✅ | Layer 4 — see §3.3 (km is canonical) |

### 3.2 Existing-equipment inputs (the "already owns X" paths)

| Field | Default | Effect on the ladder |
|---|---|---|
| `existing_pv_kwp` | 0 | If > 0: Layer 1 adds capacity only up to roof cap; **capex on the added kWp only**; production on **total** installed; the current bill already reflects existing self-consumption, so Layer 1 credits only the *incremental* generation (no double-count). If existing PV already covers the need, the ladder effectively **starts at Layer 2**. |
| `existing_battery_kwh` | 0 | If > 0: Layer 2 adds only the delta; arbitrage + self-consumption on **total** battery. |
| `existing_heatpump_year` | null | `null` ⇒ no HP (fossil case). If set: an HP exists. **Old/inefficient** (age ≥ 12 yrs *or* est. SCOP < 3.0) ⇒ Layer 3 becomes an **efficiency-upgrade** offer (replace with a state-of-the-art high-SCOP unit, §5.3 Case B). **Modern/efficient** ⇒ Layer 3 Δ = 0 (not offered). |
| `existing_ev` | false | `true` ⇒ the household already drives electric (mobility baseline is *charging cost*, not fuel). |
| `existing_ev_charger` | false | `true` ⇒ a home wallbox exists. **EV + no charger** ⇒ Layer 4 becomes a **charger-only** offer (cheap home charging vs expensive public, §5.4 Case B). **EV + charger** ⇒ Layer 4 Δ = 0. |

**Layer-offer matrix (which state unlocks which layer):**

| State | Layer 3 (Heat pump) | Layer 4 (EV charger) |
|---|---|---|
| Fossil heating (OIL/GAS) | ✅ Case A — fossil → new HP | — |
| Old heat pump (age ≥ 12 / SCOP < 3) | ✅ **Case B — efficiency upgrade** | — |
| Modern heat pump | ⛔ Δ = 0 | — |
| District heating | ⛔ (out of scope for v1) | — |
| Petrol/diesel car | — | ✅ Case A — petrol → EV (charging swap) |
| **EV, no home charger** | — | ✅ **Case B — add wallbox (charging-cost swap)** |
| EV + home charger | — | ⛔ Δ = 0 |
| No car (NONE) | — | ⛔ Δ = 0 |

The configurator (§6/§9) renders owned items as **"already installed ✓ — no capex"**, so the saving is
never inflated by charging for hardware the household already has.

### 3.3 Mobility is km-based

```
# canonical internal quantity = km_year. If the user gives km, use it directly (any kind).
if mobility.km_month given:
    km_year = mobility.km_month × 12
elif mobility.eur_month given:
    if kind ∈ {PETROL, DIESEL}:                       # € is fuel spend
        litres_year = eur_month × 12 / fuel_price_per_litre[kind]
        km_year     = litres_year / consumption_l_per_100km[kind] × 100
    elif kind == EV:                                  # € is current charging spend (public price)
        kwh_year = eur_month × 12 / public_charge_per_kwh
        km_year  = kwh_year / ev_consumption_kwh_per_100km × 100
```
Everything in Layer 4 then derives from `km_year`. Defaults (all from `price_catalog`, §12): petrol
€1.85/L @ 7.0 L/100 km, diesel €1.75/L @ 6.0 L/100 km, EV 18 kWh/100 km, public charge €0.45/kWh.

### 3.4 UX rules

Progressive disclosure: ask the mandatory set, derive the rest, let power users refine. Every missing
optional field is filled by a **labelled assumption** the user can override (overrides tighten the
confidence band). Two intake modes, one schema: **form** (Zod) and **conversational LLM**. Never block
the result on missing data — degrade to defaults and flag uncertainty.

---

## 4. Pre-step — Site-Check: permits & obligations (nationally correct)

> In 2026 German law *privileges* renewables (EEG §2). Roof-PV, air-source heat pumps and wallboxes
> are **verfahrensfrei** (no building permit) in essentially every Land's building code. Site-Check is
> therefore a fast **feasibility + obligations** check, not a gate-keeper. It needs the **full address**
> (hence street + nr is mandatory).

| Product | Check | Source (national) | Result logic |
|---|---|---|---|
| Solar PV | Building permit | LBO — roof PV verfahrensfrei | 🟢 No permit needed |
| Solar PV | **Heritage (Denkmalschutz)** ← only real gate | Länder Denkmal datasets / user confirm | 🟢 Not listed / 🟡 Listed → approval |
| Solar PV | Neighbour precedent (social proof) | MaStR (seeded by PLZ) | 🟢 40+ / 🟡 5–40 / ⚪ unknown |
| Heat pump | GEG compliance | Hardcoded rule (GEG §71) | 🟢 Always compliant |
| Heat pump | Old-boiler **opportunity** | `heating ∈ {OIL,GAS}` | ℹ️ KfW-subsidised + may become mandatory (timeline) |
| Heat pump | Outdoor-unit noise | TA Lärm advisory (~3 m to boundary) | 🟢 OK / 🟡 Tight plot |
| EV charger | Right to install | §20 WEG / §554 BGB (since 1 Dec 2020) | 🟢 Legal *right* — apartment community decides only the *how* |
| EV charger | Private parking | OSM tag + user checkbox | 🟢 Driveway/garage / 🟡 Street-only → public-charge fallback |
| EV charger | Grid registration | Hardcoded | ℹ️ ≤11 kW notify Netzbetreiber · >11 kW approval |
| Battery | Installation | Hardcoded | 🟢 Indoor, verfahrensfrei |
| Battery | Grid registration | Hardcoded | ℹ️ Register in MaStR within 1 month |

**GEG 2024 timeline** (drives heat-pump urgency, not a block): new heatings must be ≥65% renewable;
for existing buildings the duty couples to municipal heat planning — large municipalities (>100 k) by
**30 Jun 2026**, the rest by **30 Jun 2028**. Working boilers may keep running; constant-temperature
boilers >30 years must be decommissioned (§72, owner-occupied exceptions).
[GEG (official).](https://www.gesetze-im-internet.de/geg/)

**Data reality:** Denkmalschutz has no single national API (Länder competence; Bavaria's DenkmalAtlas
is live WFS) → fall back to a "Is your home listed?" checkbox. MaStR has no clean count-by-PLZ REST →
seed counts for demo PLZs from the public Gesamtdatenexport; elsewhere ⚪ "unknown" (social proof
only). OSM Overpass (parking/building type) is free.

---

## 5. The four upgrade layers (the comparison core)

Each layer is a pure module. It is always computed **on the running state** (everything ticked below
it), and it reports a **bucket €/month** that feeds the configurator (§6).

### 5.1 Layer 1 — `+ Solar / PV`  (Electricity bucket)

```
# Sizing — from contract package tier, roof geometry, or matched to final-bundle load:
panels        = usable_roof_m2 / module_area_m2          # module_area from price_catalog (≈1.95 m²)
gross_kwp     = panels × module_kwp                      # module_kwp from price_catalog (≈0.44)
added_kwp     = max(0, recommended_kwp − existing_pv_kwp)    # ← existing PV handled here
total_kwp     = existing_pv_kwp + added_kwp
# Tier fallback (no geometry): SMALL≈6 · MEDIUM≈9 · LARGE≈12 kWp

# Annual yield — PVGIS PVcalc (live, official EU JRC), constant fallback:
GET https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?lat=..&lon=..&peakpower=<total_kwp>
    &loss=14&mountingplace=building&angle=<tilt|35>&aspect=<azimuth|0>&outputformat=json
→ annual_yield_kwh = outputs.totals.fixed.E_y            # includes PR/losses
Fallback: annual_yield_kwh = total_kwp × specific_yield(PLZ)   # ≈980 kWh/kWp DE

# Self-consumption is LOAD-AWARE (the key correctness fix — see §8.1):
self_consumed_kwh = autarky_factor × annual_consumption_kwh        # capped ≤ annual_yield
exported_kwh      = annual_yield_kwh − self_consumed_kwh
  # autarky_factor: 0.30 PV-only; rises with battery (L2) and added flexible load (L3/L4)
  # annual_consumption_kwh accumulates across layers: base + HP elec (L3) + EV kWh (L4)

elec_saving_self = self_consumed_kwh × retail_price                 # displaced grid import
elec_feedin_rev  = exported_kwh      × 0.0778                       # ✅ EEG ≤10 kWp (Bundesnetzagentur)
LAYER-1 electricity bucket €/mo = (elec_saving_self + elec_feedin_rev) / 12
# If existing_pv_kwp > 0: credit only the incremental yield's self-consumption + feed-in.
```

### 5.2 Layer 2 — `+ Battery`  (Electricity bucket, second value stream)

```
added_kwh   = max(0, recommended_batt_kwh − existing_battery_kwh)   # existing battery handled here
total_kwh   = existing_battery_kwh + added_kwh

# (a) Extra self-consumption: battery lifts autarky 0.30 → ~0.60 (shift midday surplus to evening)
extra_self_kwh   = (autarky_with_batt − autarky_pv_only) × annual_consumption_kwh     # ≤ unused yield
extra_self_value = extra_self_kwh × retail_price − extra_self_kwh × 0.0778  # net of lost feed-in
# (b) Dynamic-tariff arbitrage: charge cheap hours, discharge expensive hours (see §7 dynamic tariff)
arbitrage_value  = total_kwh × cycles_per_year × round_trip × dynamic_spread
                   # cycles≈300, round_trip≈0.90, dynamic_spread from SMARD/EPEX day-ahead (§7)

LAYER-2 electricity bucket €/mo += (extra_self_value + arbitrage_value) / 12
```
No double-counting: PV charges the battery first (counts as self-consumption); only the *remaining*
cycles are pure arbitrage, on their own line with a wider confidence band. Arbitrage is credited
**only** on the dynamic tariff — which is part of the Cloover bundle.

### 5.3 Layer 3 — `+ Heat pump`  (Heating bucket)

**Offered in two states** (see the offer matrix, §3.2): **Case A** = current fuel ∈ {OIL, GAS}
(fossil → new HP); **Case B** = an **old/inefficient heat pump** already exists (upgrade to a
state-of-the-art high-SCOP unit). Both share the same heat-demand and running-cost maths; they differ
only in the *baseline* they replace and the *subsidy* available.

```
# Heat demand (kWh/yr) — independent of the current heating system:
#   Case A primary (from ACTUAL fuel spend, most credible):
#     OIL: 10.0 kWh/L gross × 0.85 boiler η = 8.5 kWh useful/L; oil price from price_catalog
#     GAS: ≈ €0.115/kWh all-in × 0.90 η
#     heat_demand_kwh = (heating_eur_month × 12 / fuel_unit_price) × boiler_efficiency × calorific
#   Case B (old HP): back out demand from the old unit's electricity:
#     heat_demand_kwh = (heating_eur_month × 12 / retail_price) × old_SCOP
#       old_SCOP ≈ 2.8 default (age ≥ 12 yrs / pre-2014 air-source); refine from existing_heatpump_year
#   Fallback for either (area method, uses floor_area + building_year):
#     heat_load_W_m2 = lookup(building_year)  # §10 table
#     required_kW = ceil_to(6/8/.../16, heat_load_W_m2 × floor_area_m2 / 1000)
#     heat_demand_kwh = required_kW × 1800 full-load hours

new_SCOP = 3.5 (Case A, conservative air-source) … 4.0 (Case B, state-of-the-art target)
hp_electricity_kwh = heat_demand_kwh / new_SCOP        # Case B deliberately picks the higher SCOP
annual_consumption_kwh += hp_electricity_kwh           # ← raises L1/L2 self-consumption value
solar_covered_kwh  = hp_electricity_kwh × overlap      # 0.15 PV-only · 0.30 +battery (winter-weak)
hp_grid_kwh        = hp_electricity_kwh − solar_covered_kwh
heating_new_cost   = hp_grid_kwh × retail_price / 12

# Baseline that the new HP replaces:
#   Case A: heating_eur_month (current fossil fuel spend)
#   Case B: old_hp_running_cost = heat_demand_kwh / old_SCOP × retail_price / 12   (= current HP elec spend)
LAYER-3 heating bucket €/mo = baseline_heating_cost − heating_new_cost
```

- **Case B saving driver** = the efficiency delta only: `heat_demand × (1/old_SCOP − 1/new_SCOP) ×
  retail_price`. It is **smaller** than a fossil swap, so it is only recommended when the optimiser
  finds it net-positive against the new-HP installment — honest by construction (an old but *modern-
  enough* HP yields Δ ≈ 0 and is not offered).
- **KfW nuance (Case B):** replacing one heat pump with another does **not** qualify for the
  Klima-Geschwindigkeitsbonus (that requires removing a fossil/old non-renewable system). So Case B's
  modelled grant is the base 30 % (+ income/efficiency bonuses only), not 50 % — see §6.5.

Honest interaction: the heat pump's winter load coincides poorly with PV, so `overlap` is low — but its
electricity demand still lifts the value of the PV+battery from Layers 1–2.

### 5.4 Layer 4 — `+ EV charger`  (Mobility bucket)

**Offered in two states** (offer matrix, §3.2): **Case A** = current car ∈ {PETROL, DIESEL}
(petrol → EV; the saving is fuel → cheap charging). **Case B** = household **already drives an EV but
has no home charger** (`existing_ev ∧ ¬existing_ev_charger`); adding a wallbox swaps *expensive public
charging* for *cheap home charging* (PV surplus / off-peak dynamic tariff). Both compute the same
`ev_kwh_year`; they differ only in the baseline cost being displaced and the capex (Case B is the
wallbox alone — no vehicle assumed).

```
# Energy need — km is canonical (intake §3.3). For an existing EV, km may be given directly,
# or backed out of the current charging spend at the public price.
ev_kwh_year = km_year × ev_consumption_kwh_per_100km / 100          # EV ≈ 18 kWh/100 km
annual_consumption_kwh += ev_kwh_year                              # ← flexible load, big self-cons. uplift
home_charge_cost = ev_kwh_year × home_blended_price                 # ≈ €0.20/kWh (blend below)

# Baseline being displaced:
#   Case A (petrol/diesel): current_fuel_cost = km_year/100 × consumption_l_per_100km × fuel_price
#   Case B (EV, no charger): current_charge_cost = ev_kwh_year × public_charge_price   # ≈ €0.45/kWh public avg
LAYER-4 mobility bucket €/mo = baseline_mobility_cost / 12 − home_charge_cost / 12
```

- **`home_blended_price` ≈ €0.20/kWh** = PV surplus (≈ free, ~40 %) + off-peak dynamic tariff (~50 %) +
  occasional public DC (~10 %); charging is **scheduled into the cheapest dynamic-tariff hours** (§7).
- **Case B economics:** the saving is purely the price gap `public_charge_price − home_blended_price`
  (≈ €0.45 → €0.20) over `ev_kwh_year`, against a small wallbox capex — usually strongly net-positive
  for any real annual mileage, which is why it is worth surfacing as its own offer.
- If Site-Check found **street-only parking** (no private wallbox possible), Layer 4 is **not offered**
  (Case B) or drops the PV share so the blend rises (~€0.30) and the saving shrinks honestly (Case A).

---

## 6. The incremental configurator (Check24-style) + optimiser + financing

### 6.1 Marginal math (sums exactly to the headline)

```
state₀ = baseline (minus any already-owned equipment, §3.2)
for each layer added in order L1→L2→L3→L4 (skipping already-owned):
    stateₙ = stateₙ₋₁ + layer
    Δ_gross(layer)       = gross_saving(stateₙ) − gross_saving(stateₙ₋₁)   # on the running state
    Δ_capex(layer)       = capex_after_subsidy(layer)        # from price_catalog (§12), only the delta
    Δ_installment(layer) = annuity(Δ_capex, annual_rate, term_months)
    Δ_net(layer)         = Δ_gross − Δ_installment           # what THIS layer adds to the saving
    cumulative_net       = Σ Δ_net   = monthly_saving (North Star) for the current selection
```
Canonical-order marginals **sum exactly** to the headline saving → every toggle row is honest.

### 6.2 The interaction that makes it credible

Later layers raise `annual_consumption_kwh`, which lifts the self-consumption value of the PV+battery
already installed (Layers 1–2 are re-evaluated on the running state). This is *why a bigger upgrade can
raise the monthly saving*, and the literal challenge answer.

### 6.3 Dependency & toggle rules

| Layer | Depends on | Standalone allowed? | **Offered when** (else hidden, Δ = 0) |
|---|---|---|---|
| L1 ☀️ Solar | — | yes | roof_ok **and** `existing_pv_kwp` below roof cap (adds the delta) |
| L2 🔋 Battery | recommends L1 | yes (still arbitrages grid on the dynamic tariff) | `existing_battery_kwh` below recommended (adds the delta); nudge "add PV to unlock self-consumption" |
| L3 ♨️ Heat pump | — | yes (fossil→electricity saves alone) | **Case A:** heating ∈ {OIL, GAS} · **Case B:** old/inefficient HP (age ≥ 12 yrs or SCOP < 3.0) → efficiency upgrade. Hidden for a modern HP or district heating. |
| L4 🚗 EV charger | — | yes | **Case A:** car ∈ {PETROL, DIESEL} · **Case B:** `existing_ev ∧ ¬existing_ev_charger` (cheap home charging vs public). Hidden if EV already has a charger, NONE, or street-only parking. |

Recommended product = the strict nested ladder (= the 4 contract scenarios). À-la-carte (any subset,
≤16 pure evaluations) is a cheap **stretch** mode.

### 6.4 Optimiser & up-sell

`recommend()` walks the ladder and returns the rung with the **largest `monthly_saving`** (not
necessarily the deepest — a layer whose installment outweighs its saving is skipped). Up-sell = a diff
vs the next-smaller rung, surfaced inline: *"Going from PV+battery (−€24/mo) to the full bundle lands
**+€120/mo** — because you're still burning oil + petrol that the heat pump and EV displace."*

### 6.5 Financing overlay (the anchor) — **official sources**

```
capex_after_subsidy = capex − subsidies
   PV + battery:  0 % VAT already (§12(3) UStG, since 2023) → no further federal grant assumed
   heat pump A:   fossil → HP — KfW 458 — 30 % base + bonuses, capped 70 % of eligible cost
                  (cap €30,000 → max €21,000; a 2026 efficiency bonus may lift toward €23,500).
                  Default modelled 50 % (base 30 % + Klima-Geschwindigkeitsbonus 20 %).
   heat pump B:   old HP → new HP — **no Klima-bonus** (needs a fossil/non-renewable removal),
                  so default modelled **30 %** (base; + income/efficiency bonuses if applicable).
   EV charger:    €0 (Umweltbonus ended 17 Dec 2023, BAFA) — wallbox capex only (no vehicle financed)
installment = annuity(capex_after_subsidy − downpayment, annual_rate, term_months)
              # contract defaults: term 180 mo, APR 5 % — REPLACE with Cloover's real product (confirm)
monthly_saving      = gross_saving − installment        # North Star (honest: may be ≈0/neg early)
saving_after_payoff = gross_saving
break_even_month    = first month cumulative_net ≥ 0
```
Sources: [KfW 458 (official)](https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/Förderprodukte/Heizungsförderung-für-Privatpersonen-Wohngebäude-(458)/) ·
[EEG feed-in — Bundesnetzagentur](https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/ErneuerbareEnergien/EEG_Foerderung/start.html) ·
[Umweltbonus ended — BAFA](https://www.bafa.de/DE/Energie/Energieeffizienz/Elektromobilitaet/elektromobilitaet_node.html).

---

## 7. Savings certainty (the four drivers — required by the challenge)

The challenge names four certainty drivers. Each is modelled with a real source and a confidence
treatment:

| Driver | How we get it | Layer used | Confidence treatment |
|---|---|---|---|
| **Local irradiance** | PVGIS per **lat/lon** (from the mandatory street address) | L1 | ±8 % band; tightened by roof tilt/azimuth override |
| **Dynamic tariff** *(emphasised)* | **SMARD / EPEX day-ahead** hourly prices (official) — see below | L2 (arbitrage), L4 (EV scheduling) | widest band; spot spread varies → shown on its own line |
| **Applicable subsidies** | KfW 458 eligibility (boiler age, owner-occupier, income bonus) | L3 financing | modelled 50 %, range 30–70 % shown |
| **Self-consumption ratio** | load-aware autarky model, lifted by L2/L3/L4 load | L1, L2 | the single biggest driver → named in the UI band |

### 7.1 Dynamic tariff model (the heart of the Cloover story)

The bundle assumes the household **switches to a dynamic (day-ahead) tariff**, so flexible load and the
battery earn the spot spread.

```
# Hourly day-ahead prices (official, free):
#   SMARD:        https://www.smard.de/app/chart_data/{filter}/{region}/index_hour.json   (Bundesnetzagentur)
#   Energy-Charts (Fraunhofer ISE): https://api.energy-charts.info/price?bzn=DE-LU
#   aWATTar:      https://api.awattar.de/v1/marketdata    (DE, free) — EPEX day-ahead
effective_consumer_price(hour) = day_ahead_price(hour) + fixed_components   # taxes, levies, grid, margin
dynamic_spread = mean(price of priciest N hours) − mean(price of cheapest N hours)   # net usable spread
# Uses:
#   Battery (L2): charge cheapest hours → discharge priciest → arbitrage_value (§5.2)
#   EV (L4):      schedule charging into the cheapest hours → low blended_charge_price (§5.4)
#   Heat pump (L3): optional load-shift of the buffer tank into cheap hours (stretch)
```
MVP uses a **seeded representative spread (€0.12/kWh net)** from recent SMARD data; the live SMARD/
Energy-Charts pull is a toggle. The spot spread carries the widest band → arbitrage is always shown on
its own line, never blended into the "certain" buckets.

---

## 8. Worked example (corrected & transparent)

Detached DE home, 3 people · €95 electricity · €180 oil · €160 petrol = **baseline €435/mo**.
PV 9 kWp · battery 8 kWh · air-source HP · wallbox. Financing 180 mo @ 5 %.
Derived physical quantities: base load 3,081 kWh/yr · HP electricity 4,769 kWh/yr · EV 2,668 kWh/yr
(14,800 km) · PV yield 8,820 kWh/yr.

| Step you add | + Capex (after subsidy) | + Installment | Δ gross /mo (on running state) | **Δ net /mo** | Cumul. net **now** | After payoff |
|---|---:|---:|---:|---:|---:|---:|
| ☀️ + Solar 9 kWp | €13,050 (0 % VAT) | €103 | +€80 | **−€24** | −€24 | €80 |
| 🔋 + Battery 8 kWh | €5,600 | €44 | +€44 | **≈ €0** | −€24 | €124 |
| ♨️ + Heat pump | €11,000 (€22k − 50 % KfW) | €87 | +€107 | **+€20** | −€4 | €230 |
| 🚗 + EV charger | €1,200 | €10 | +€133 | **+€124** | **+€120** | €364 |

**Reading (the honest Cloover pitch):** solar *alone* on this small base load is mildly negative —
today's 7.78 ct feed-in means an oversized array mostly exports cheaply. The value appears when you
**electrify the loads** (heat pump + EV) so the solar is actually *self-consumed*: the full bundle nets
**≈ €120/mo from day one** and **≈ €364/mo after the loan is paid off**. The optimiser recommends the
**full ladder**. EV is the single biggest saver here because petrol is expensive vs cheap off-peak/PV
charging. (Illustrative; the TDD'd engine + live data produce the exact figures.)

### 8.1 Why the battery is ≈ €0/mo here (not −€20 — the v0.2 error, re-checked)

The earlier "−€20/mo" **under-counted** the battery's value. Re-derived transparently at the battery
rung (base load 3,081 kWh/yr, before HP/EV load is added):

```
(a) Extra self-consumption: autarky 0.30 → 0.60 ⇒ +0.30 × 3,081 = +924 kWh × €0.37   = +€342/yr
(b) Less feed-in (stored, not exported):                      −924 kWh × €0.0778      =  −€72/yr
(c) Dynamic-tariff arbitrage: 8 kWh × 300 cycles × 0.90 × €0.12 spread                = +€259/yr
    ── battery gross  = 342 − 72 + 259                                                = +€529/yr  = +€44/mo
    ── installment (€5,600 @ 5 % / 180 mo)                                            = −€44/mo
    ── NET at this rung                                                               ≈  €0/mo
```

**Is that realistic? Yes — and here's the mechanism.** A standalone home battery in Germany 2026 is
*roughly break-even*: ~half its value is extra self-consumption, ~half is day-ahead arbitrage, and
that almost exactly offsets a €44/mo financed cost. The number is *low precisely because the base load
is small* — without the heat pump and EV there is little extra load for the stored energy to displace.
**Add Layers 3–4 (≈ 7,400 kWh of new annual load) and the same battery cycles displace far more
expensive grid import → its value climbs well above its installment.** This is the cumulative
interaction (§6.2) made concrete: the battery is the enabler that pays off once the loads are
electrified — which is exactly the bundle Cloover wants to sell. (The original −€20 assumed a smaller
gross of ~€24/mo; it had dropped the arbitrage line and used a lower self-consumption uplift.)

---

## 9. Dashboard — a live configurator

- **YOUR SAVING: €X / month** — biggest text; recomputes as layers toggle.
- **Four layer rows (Check24-style), in order**, each showing its own contribution + capex; owned
  items shown as installed (no capex):
  ```
  ☀️ Solar 9 kWp        −€24/mo    (€13,050 · 0 % VAT)         [ ✓ ]
  🔋 Battery 8 kWh       ≈ €0/mo    (€5,600)                   [ ✓ ]   ← break-even now, pays off as load grows
  ♨️ Heat pump          +€20/mo    (€22k − €11k KfW 458)       [ ✓ ]   ← "still on oil? this layer"
  🚗 EV charger         +€124/mo    (€1,200)                   [ ✓ ]
  ────────────────────────────────────────────────
  TOTAL  +€120/mo now  →  €364/mo after payoff   ±€35
  ```
- **Honest curve:** *"≈ cost-neutral early → €364/mo once the loan is paid off"* + break-even year.
- Before vs after: *"Today €435/mo → with the bundle €Z/mo."*
- Permits panel: all green ✓ (Site-Check), with the one real flag if present.
- Free with the bundle: smart meter, **dynamic tariff**, Cloover energy manager.
- Confidence chip `±€` + biggest-driver line. Assumptions drawer (editable → live re-run).
- **Claude paragraph** in plain German: 3 sentences on why *this* config fits *this* home.
- Green CTA: **Apply for Cloover financing**.

**90-sec demo:** type address + 5 numbers → solar number appears → tick 🔋 (≈€0, honest) → tick ♨️ + 🚗
(number jumps with the up-sell line) → edit one assumption → band tightens → "Generate proposal".

---

## 10. Reference dataset — **with where each item is used**

> Seed into Supabase so the demo runs offline; live PVGIS/SMARD are a toggle. `verify@build` = refresh
> the value at setup. **"Used in"** names the exact layer/step that consumes it — so it is clear no row
> is dead weight.

| Constant | Value (2026) | Official / primary source | **Used in (layer · step)** |
|---|---|---|---|
| Specific PV yield (DE) | live per lat/lon; fb **980** kWh/kWp | PVGIS (EU JRC) | **L1** · annual_yield |
| Self-consumption autarky | 0.30 PV-only · ~0.60 +batt (load-aware) | BSW/HTW Berlin studies | **L1, L2** · self_consumed_kwh |
| Retail electricity price → *stored in `price_catalog` §12* | **€0.37**/kWh (+ per-PLZ grid fee) | Destatis / BNetzA | **L1–L4** · grid import & displaced cost |
| **Feed-in (≤10 kWp)** → *stored in `price_catalog` §12* | **€0.0778**/kWh (1 Feb–31 Jul 2026) | **Bundesnetzagentur** | **L1** · elec_feedin_rev |
| Dynamic-tariff spread (net) | **€0.12**/kWh (seeded; live toggle) | **SMARD / EPEX** | **L2** arbitrage · **L4** EV scheduling |
| Battery cycles/yr · round-trip | **300** · **0.90** | engineering / datasheets | **L2** · arbitrage_value |
| Heating oil | 10.0 kWh/L · η 0.85 | Destatis / DIN | **L3** · heat_demand |
| Gas all-in price · η | €0.115/kWh · 0.90 | Destatis | **L3** · heat_demand |
| Heat pump SCOP — new | **4.0** state-of-the-art (3.5–4.5); 3.5 baseline air-source | manufacturer JAZ / BWP | **L3** · hp_electricity (both cases) |
| Heat pump SCOP — old (Case B) | **2.8** (age ≥ 12 yr / pre-2014); refine from install year | BWP / field data | **L3** Case B · old_hp baseline |
| PV→HP overlap | 0.15 PV-only · 0.30 +batt | engineering | **L3** · solar_covered |
| Heat-load by Baujahr (W/m²) | 150 (<1977) … 40 (>2016) | IWU/TABULA | **L3** · area-method fallback |
| Full-load hours (heating) | **1800** h | DE single-family norm | **L3** · area-method fallback |
| Petrol / diesel consumption | 7.0 / 6.0 L/100 km | class default / ADAC | **Intake §3.3** · €→km · **L4** |
| EV consumption | **18** kWh/100 km | class default | **L4** · ev_kwh_year |
| EV home blended charge | **€0.20**/kWh | derived (PV+off-peak+public) | **L4** · home_charge_cost (both cases) |
| EV public charge price | **€0.45**/kWh | CPO public AC/DC avg (Destatis/Ladesäulenregister) | **L4** Case B · public baseline |
| **KfW 458 grant** | 30 % base → max **70 % / €21,000** | **KfW (official)** | **§6.5** financing · L3 capex |
| PV/battery VAT | **0 %** (§12(3) UStG) | UStG (official) | **§6.5** · L1/L2 capex |
| EV purchase grant | **€0** (Umweltbonus ended 2023) | **BAFA (official)** | **§6.5** · L4 |
| Financing APR · term | 5 % · 180 mo (**Cloover real TBC**) | Cloover product | **§6.5** annuity |

> **Split of concerns:** every **monetary price** (PV €/kWp, battery €/kWh, HP, wallbox, fuel, retail
> €/kWh, feed-in €/kWh) physically lives in the **`price_catalog` DB (§12)** and is read at request
> time — never hard-coded. This table holds the **physics/policy constants** (yields, ratios, SCOP,
> subsidy %, VAT); the two price rows above are shown only to map *where they are used*.

---

## 11. Data sources — what each is and where it plugs in

| Source | What it is / endpoint | Auth | **Plugs into (layer · step)** | Fallback |
|---|---|---|---|---|
| **PVGIS** (EU JRC) | Free solar-yield API · `re.jrc.ec.europa.eu/api/v5_2/PVcalc` | none | **L1** · annual_yield_kwh | constant 980 |
| **SMARD** (Bundesnetzagentur) | Official day-ahead price JSON · `smard.de/app/chart_data/...` | none | **L2** arbitrage spread · **L4** EV scheduling · **§7** | seeded €0.12 |
| **Energy-Charts** (Fraunhofer ISE) | Day-ahead price API · `api.energy-charts.info/price` | none | same as SMARD (alt source) | SMARD |
| **aWATTar** | Day-ahead market data · `api.awattar.de/v1/marketdata` | none | same as SMARD (alt source) | SMARD |
| **Google Solar** | Roof geometry · `solar.googleapis.com/v1/buildingInsights:findClosest` | **key+billing**, EEA caveats | **L1** · usable_roof_m2 (precision) | PVGIS + area heuristic |
| **OSM Overpass** | Parking / building type · `overpass-api.de/api/interpreter` | none | **Site-Check** · EV parking | user checkbox |
| **Denkmalschutz** (Länder WFS) | Heritage-listing geodata (Bavaria live) | varies | **Site-Check** · solar/HP heritage flag | user checkbox |
| **MaStR** | Installed-systems register · Gesamtdatenexport | export | **Site-Check** · neighbour precedent | ⚪ unknown |
| **Netztransparenz / BNetzA** | Grid fees per DSO/PLZ (CSV) | public | **Resolver** · retail_price per PLZ | flat €0.37 |
| **Destatis** | Official energy & fuel price index | public | **price_catalog** seed (§12) | seeded constants |
| **KfW / BAFA / GEG** | Subsidy & policy (official sites) | — | **§6.5** financing | §10 constants |
| **Anthropic (Claude)** | Advisor LLM (server-side) | key (FastAPI) | **Advisor** · prose only | OpenAI adapter |

> ⚠️ **Security:** Google Solar, Anthropic, Supabase service-role keys live **only** in FastAPI's env.
> The Vite bundle ships one var: `VITE_API_BASE_URL`.

---

## 12. Pricing — DB-driven `price_catalog` (no hard-coded prices)

> Feedback: product unit prices must **not** be hard-coded; they must be read from a database. The
> domain stays pure — prices are **injected** into the engine via a `PricingContext` the resolver
> builds from this table, never imported.

**Supabase table `price_catalog`** (seed now, editable later without code changes):

```
price_catalog(
  component   text,    -- 'pv_per_kwp' | 'battery_per_kwh' | 'heatpump_fixed' | 'wallbox_fixed'
                       --  'oil_per_litre' | 'gas_per_kwh' | 'petrol_per_litre' | 'diesel_per_litre'
                       --  'retail_per_kwh' | 'feedin_per_kwh' | 'public_charge_per_kwh'
  tier        text,    -- 'SMALL'|'MEDIUM'|'LARGE'|null   (size-dependent pricing)
  unit        text,    -- 'EUR/kWp' | 'EUR/kWh' | 'EUR' | 'EUR/l' ...
  unit_price  numeric,
  source      text,    -- official/market reference (URL or 'Destatis 2026-06', etc.)
  valid_from  date,
  PRIMARY KEY (component, tier, valid_from)
)
```

**Seed values (market 2026, clearly labelled — refine before demo, but managed centrally not inline):**

| component | tier | unit_price | source note |
|---|---|---|---|
| `pv_per_kwp` | SMALL | €1,450 | market quote avg; 0 % VAT |
| `pv_per_kwp` | LARGE | €1,300 | economies of scale |
| `battery_per_kwh` | — | €700 | usable-kWh market avg |
| `heatpump_fixed` | — | €22,000 | air-source incl. install (range 18–30k) |
| `wallbox_fixed` | — | €1,200 | incl. install |
| `oil_per_litre` | — | €1.10 | Destatis heating-oil index |
| `gas_per_kwh` | — | €0.115 | Destatis gas index |
| `petrol_per_litre` | — | €1.85 | Destatis / ADAC |
| `diesel_per_litre` | — | €1.75 | Destatis / ADAC |
| `retail_per_kwh` | — | €0.37 | Destatis (per-PLZ grid fee overlay) |
| `feedin_per_kwh` | — | €0.0778 | Bundesnetzagentur EEG |
| `public_charge_per_kwh` | — | €0.45 | public CPO avg (L4 Case B baseline) |

Flow: **Resolver reads `price_catalog` (+ per-PLZ overlays) → builds `PricingContext` → injects into the
pure engine.** Capex in §6.1 (`Δ_capex`) and every €/kWh in Layers 1–4 come from here. Changing a price
= one DB row, no redeploy.

---

## 13. Resource lists

### 13.1 Comprehensive list — everything available & verified usable

| # | Resource | Type | Auth | Verified available |
|---|---|---|---|---|
| 1 | PVGIS (EU JRC) | Solar yield API | none | ✅ free, no key |
| 2 | SMARD (Bundesnetzagentur) | Day-ahead price JSON | none | ✅ official, documented JSON |
| 3 | Energy-Charts (Fraunhofer ISE) | Day-ahead price API | none | ✅ free |
| 4 | aWATTar | Day-ahead market API | none | ✅ free (DE) |
| 5 | Google Solar API | Roof geometry | key+billing | ⚠️ DE MEDIUM coverage; EEA field caveats |
| 6 | OSM Overpass | Parking/building geodata | none | ✅ free |
| 7 | Denkmalschutz (Länder WFS) | Heritage geodata | varies | 🟡 Bavaria live; others vary |
| 8 | MaStR Gesamtdatenexport | Installed-systems register | export | 🟡 bulk export (no count REST) |
| 9 | Netztransparenz / BNetzA | Grid fees per PLZ | public CSV | ✅ public |
| 10 | Destatis | Energy/fuel price indices | public | ✅ public |
| 11 | KfW 458 | Subsidy rules (official) | — | ✅ official page + Merkblatt |
| 12 | BAFA | EV-grant status (official) | — | ✅ official |
| 13 | GEG (gesetze-im-internet) | Heating law (official) | — | ✅ official |
| 14 | Anthropic Claude API | Advisor LLM | key | ✅ (credits) |
| 15 | Supabase | Postgres + auth | key | ✅ |
| 16 | BDEW H0 load profile | Hourly load shape | public | 🔵 stretch (hourly sim) |

### 13.2 Optimal list for *our* design (MVP demo — minimal, all green)

| Used for | Pick | Why this one |
|---|---|---|
| Solar yield (L1) | **PVGIS** | free, no key, demo-safe; constant 980 fallback |
| Dynamic tariff (L2/L4, §7) | **SMARD** (primary) + aWATTar (alt) | official Bundesnetzagentur data; seeded €0.12 spread for the demo |
| Subsidies / policy (§6.5) | **KfW 458 · BAFA · GEG** (seeded constants) | official, static — no live call needed |
| Prices (§12) | **`price_catalog` in Supabase** (Destatis-seeded) | DB-driven, editable, no hard-code |
| Permits (Site-Check) | **OSM Overpass** + Denkmal checkbox | free; checkbox is the national fallback |
| Roof geometry (L1) | **PVGIS + area heuristic** (Google Solar = stretch toggle) | avoids billing/EEA caveats in the demo |
| LLM advisor | **Claude** (Anthropic) | default per stack; OpenAI fallback |
| Persistence/cache | **Supabase** | reference data, price_catalog, runs, proposals |

Everything in 13.2 is either free/no-key or static-seeded → the live demo has **zero hard external
dependencies**; live PVGIS/SMARD/Google are upgrade toggles.

---

## 14. Contract & persistence

### 14.1 Engine endpoint

`POST /api/v1/advisor/recommend` → `Recommendation { best, alternatives[], upsell }`. **`alternatives[]`
= the four cumulative ladder steps**; each `ScenarioResult` carries `breakdown
{electricity,heating,mobility}_eur_month`, `installment_eur_month`, `monthly_saving_eur` (North Star),
`payback_note`. The configurator's per-layer "+€X/mo" = the difference between consecutive
`monthly_saving_eur` values (§6.1) — no extra call.

**Required contract extensions (update `openapi.yaml` in the same PR):** add to `Household` —
`address {street, house_no, city}` (mandatory), `floor_area_m2`, `building_year`, `existing_pv_kwp`,
`existing_battery_kwh`, **`existing_heatpump_year` (nullable — null ⇒ no HP)**, **`existing_ev: bool`**,
**`existing_ev_charger: bool`**, and `mobility.km_month` (alongside `eur_month`; `CarType` enum already
includes `EV`). À-la-carte stretch: optional `selection {pv,battery,heat_pump,ev}: bool`. The two new
edge cases (old-HP upgrade, EV-without-charger) need no new endpoint — they change only which layer is
*offered* and the *baseline* it replaces, both resolved server-side from these fields.

### 14.2 Enrichment endpoint

`POST /api/v1/advisor/site-check` → full address (+ `floor_area_m2`/`building_year`) → runs Site-Check
+ roof geometry → `{ roof_ok, feasibility_flags[], energy_context, assumptions[] }`. The SPA calls this
first, then `/recommend`.

### 14.3 Supabase schema

```
reference_plz   (plz PK, lat, lon, specific_yield, retail_price, grid_fee, climate_zone, mastr_count)
price_catalog   (component, tier, unit, unit_price, source, valid_from)          -- §12, DB-driven prices
cache_pvgis     (lat, lon, tilt, azimuth, kwp, payload_json, fetched_at)         -- TTL 30d
cache_dynprice  (market_area, day, payload_json, fetched_at)                     -- TTL 1d (SMARD/aWATTar)
advise_run      (id PK, household_json, options_json, recommendation_json, created_at)
proposal        (id PK, advise_run_id FK, copy_md, created_at)
denkmal_seed (plz, flag)   mastr_seed (plz, count)                               -- demo PLZs only
```

---

## 15. Risks & demo-safety

| Risk | Mitigation |
|---|---|
| Self-consumption ratio wrong → number not credible | load-aware autarky model (§5.1, §8.1); show band; cite source |
| Battery number looks implausible | transparent sub-derivation (§8.1); it is ≈ break-even by design |
| Live API flaky in demo | seed reference data + price_catalog; PVGIS/SMARD are toggles; `?fixture` path |
| LLM hallucinates a number | LLM never computes; assert every figure in the copy matches the payload |
| Over-claiming subsidies (esp. EV) | EV grant €0; KfW capped 70 %/€21k; official sources cited |
| Hard-coded prices drift | all prices in `price_catalog` (§12); one DB edit, no redeploy |
| Existing equipment double-counted | capex only on the delta; baseline already reflects owned PV (§3.2) |
| Old-HP upgrade or EV-charger offer over-sold | Case B saving = efficiency/price-gap only, no Klima-bonus for HP→HP (§5.3, §6.5); optimiser drops it if net-negative |
| Denkmal/MaStR not national | checkbox fallback; social-proof never gates |
| Secret leaks via Vite bundle | only `VITE_API_BASE_URL` client-side; all keys in FastAPI |
| Scope creep | MVP = Layers 1–4 nested ladder + KfW + LLM copy; hourly sim, Google Solar, à-la-carte, live SMARD = stretch |

---

## 16. Open decisions

1. **Market scope:** lock to Germany (recommended — all data above is DE).
2. **Configurator mode:** nested ladder (MVP) vs free à-la-carte subsets (stretch). Recommended: ladder.
3. **Denkmal demo:** Bavaria address (live API) + national checkbox (recommended: both).
4. **KfW grant default:** 50 % (base+Klima) vs 30 % conservative. Recommended: 50 %, editable.
5. **Financing APR/term:** confirm **Cloover's real product** to replace the 5 % / 180-mo default.
6. **Self-consumption fidelity:** heuristic autarky (MVP) vs 8760-h sim with BDEW H0 + SMARD (stretch).
7. **Dynamic tariff in demo:** seeded €0.12 spread (safe) vs live SMARD pull (impressive). Recommended:
   seeded for the headline, live SMARD as a visible toggle.
