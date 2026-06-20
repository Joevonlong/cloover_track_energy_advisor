# System Workflow — Heimwende Energy Advisor (Cloover track)

> **Status:** optimised & source-verified build plan · v0.2 · 2026-06-20
> **Source of truth:** [`specs/`](../../specs/) wins over this doc. This file is the *executable
> blueprint* that ties the [master plan](./heimwende-master-plan.md), the [domain spec](../../specs/domain/savings-engine.spec.md)
> and the frozen [`openapi.yaml`](../../specs/api/openapi.yaml) into one pipeline with **every data
> source, constant and formula pinned down and verified.**
> **North Star:** `monthly_saving = current_monthly_spend − (loan_installment + new_energy_cost)`.
>
> **Core interaction model (this version):** the four upgrades are an **incremental, Check24-style
> configurator** — you add `+ Solar/PV → + Battery → + Heat pump → + EV charger` one option at a
> time, and each click recomputes the single monthly number, showing exactly what *that* option adds.
> See **§5**.

---

## 0. What changed vs v0.1 (the optimisation pass)

Every item below was *wrong, stale, region-locked, or unverifiable* in the first draft and is now fixed:

1. **EV distance formula was dimensionally wrong** — it multiplied by consumption instead of
   dividing, inflating km and savings. Corrected in §4 (Layer 4).
2. **Feed-in tariff was stale** (`€0.082`). Verified current value: **7.78 ct/kWh** (partial
   feed-in, ≤10 kWp, since 1 Feb 2026). [Source.](https://www.adac.de/rund-ums-haus/energie/spartipps/einspeiseverguetung-pv-anlagen/)
3. **Permit layer was Bavaria-only** (BayernAtlas, a Bavaria Bebauungsplan RAG) — could not serve a
   national product. Replaced with a **nationally-correct legal model** (Layer 1): in 2026
   renewables are *privileged by law* (EEG §2), so roof-PV / heat-pump / wallbox are almost always
   permitted; the layer now surfaces the *few real gates* (Denkmalschutz, grid approval).
4. **GEG heat-pump rule was misstated** ("protected until 2029 🔴"). A heat pump is *always*
   GEG-compliant; the old boiler is an **opportunity** (subsidy + obligation timeline), not a block.
5. **EV apartment rule was wrong** ("owner vote needed → blocked"). Since WEMoG (1 Dec 2020) every
   owner/tenant has a **legal right** to a charge point (§20 WEG / §554 BGB); the community decides
   only *how*, never *whether*.
6. **Battery arbitrage "34% saving" was hand-wavy.** Replaced with an explicit
   `spread × cycles × round-trip` model tied to the dynamic tariff.
7. **Google Solar API was the primary roof source** — needs key, billing, and has EEA field
   restrictions since 8 Jul 2025. Demoted to *optional* enrichment behind the FastAPI proxy; **PVGIS
   (free, no key)** is the primary, demo-safe yield source.
8. **The incremental configurator is now fully specified** (§5): per-option marginal math, dependency
   rules, a worked numeric example, and the mapping onto the contract's `alternatives[]`.
9. **Stack reconciled to the decided tooling:** Vite SPA frontend, FastAPI + Supabase backend (§1) —
   including the rule that **no secret may enter the Vite bundle**.
10. **All constants are in one verified table** (§7), each with a source and a fallback; every layer
    output is mapped onto the frozen contract `POST /api/v1/advisor/recommend` (§9).

---

## 1. Tech stack & how it shapes the architecture

| Layer | Choice | Notes for this stack |
|-------|--------|----------------------|
| Frontend | **Vite + React + TS + Tailwind** (SPA) | RHF + Zod intake; TanStack Query for fetch/cache; the configurator (§5) is local state. |
| Backend | **FastAPI** (Python 3.12, `uv`) | Owns the pure domain core **and** acts as the BFF. |
| Data | **Supabase (Postgres)** | Reference dataset, response cache, persisted advise runs + proposals; optional installer auth. |
| LLM | Provider-agnostic adapter, **Claude default** | Explains/sells; **never computes** the number. |
| Contract | `specs/api/openapi.yaml` → generated TS client | FE codes against the client; BE implements the same schema. |

**The Vite switch removes the Next.js server/BFF tier.** The SPA is static files; the only server is
FastAPI. Consequences, all load-bearing:

- **FastAPI *is* the BFF.** Every third-party call (PVGIS, aWATTar, Google Solar, Anthropic) is
  server-side. The SPA only ever calls FastAPI.
- **No secret in the frontend.** Vite inlines every `VITE_*` var into the public bundle. The **only**
  frontend env var is `VITE_API_BASE_URL`. Google Solar / Anthropic / Supabase service-role keys live
  **only** in FastAPI's env.
- **CORS** allows the Vite dev origin (`http://localhost:5173`) + the deployed origin, nothing else.
- **Demo determinism:** a `?fixture=<id>` path on `/recommend` returns a frozen payload so a flaky
  upstream can never break the live demo.

```
  Vite SPA  ──HTTPS──▶  FastAPI  ──▶  domain core (pure, TDD, zero I/O)
 (no secrets)            (BFF)    └─▶  adapters ─▶ PVGIS · aWATTar · Google Solar · Anthropic
                           └────────▶  Supabase (cache · reference data · persisted runs)
```

---

## 2. End-to-end pipeline

```
 minimal   ┌────────┐   ┌──────────────┐   ┌───────────────┐   ┌─────────────────────────┐
 input  ─▶ │ INTAKE │─▶ │ SITE-CHECK   │─▶ │ RESOLVER      │─▶ │ SAVINGS ENGINE          │
 (form/LLM)│ →schema│   │ (Layer 1)    │   │ enrich §7     │   │ evaluates EVERY config  │
           └────────┘   │ permits/feas.│   │ from datasets │   │ on the running state    │
                        └──────────────┘   └───────────────┘   │ (incremental ladder §5) │
                                                               └───────────┬─────────────┘
                                                                           ▼
                              ┌──────────┐   ┌──────────────────┐   ┌──────────────┐
                     results ◀│ ADVISOR  │◀──│ CONFIGURATOR     │◀──│ OPTIMISER    │
                     +proposal│ LLM tells│   │ user toggles opts│   │ pick max net │
                              └──────────┘   └──────────────────┘   └──────────────┘
```

The Savings Engine + Optimiser are the **pure domain core** (deterministic, unit-tested). Layer 1 +
Resolver are **adapters** (I/O, cached). The Advisor is the **LLM adapter** (formats, never computes).

---

## 3. Intake — minimal in, rich model out

The **frozen contract `Household`** is the minimum that produces a number (PLZ-keyed):

| Field (contract) | Example | Drives |
|---|---|---|
| `postcode` (5-digit) | `10115` | irradiance, grid fee, climate, prices |
| `occupants` | `3` | load profile / consumption scaling |
| `electricity_eur_month` | `95` | electricity baseline |
| `heating {fuel, eur_month}` | `OIL, 180` | heating baseline + HP upside |
| `mobility {kind, eur_month}` | `PETROL, 160` | mobility baseline + EV upside |
| `roof_ok` | `true` | gates the PV options |

**Tier-1 enrichment (optional):** full street address (Layer-1 permits + Google Solar geometry),
`floor_area_m2`, `building_year`, roof orientation/tilt, annual km. These are **not** in the frozen
`/recommend` contract — they belong to a separate **`POST /api/v1/advisor/site-check`** endpoint
(§9.2) that resolves them to `roof_ok` + an `EnergyContext` + a feasibility report, keeping the pure
domain contract stable. Every missing field is filled by a **labelled assumption** the user can
override. Two intake modes, one schema: **form** (Zod) and **conversational LLM**. Never block on
missing data — degrade to defaults, flag uncertainty.

---

## Layer 1 — Site-Check: permits & obligations (nationally correct)

> **Reframe (the key fix):** in 2026 German law *privileges* renewables (EEG §2). Roof-PV,
> air-source heat pumps and wallboxes are **verfahrensfrei** (no building permit) in essentially every
> Land's building code. Layer 1 is therefore **not** a gate-keeper — it is a fast **feasibility +
> obligations** check that surfaces the *few* real constraints and turns the rest into green ticks.

| Product | Check | Source (national) | Result logic |
|---|---|---|---|
| Solar PV | Building permit | LBO — roof PV verfahrensfrei | 🟢 No permit needed |
| Solar PV | **Heritage (Denkmalschutz)** ← only real gate | Länder Denkmal datasets / user confirm | 🟢 Not listed / 🟡 Listed → approval |
| Solar PV | Neighbour precedent (social proof, not legal) | MaStR (seeded by PLZ) | 🟢 40+ / 🟡 5–40 / ⚪ unknown |
| Heat pump | GEG compliance | Hardcoded (GEG 2024 §71) | 🟢 Always compliant |
| Heat pump | Old-boiler **opportunity** | `heating ∈ {OIL,GAS}` | ℹ️ Subsidised (KfW 458) + may become mandatory (timeline) |
| Heat pump | Outdoor-unit noise | TA Lärm advisory (~3 m to boundary) | 🟢 OK / 🟡 Tight plot → siting note |
| EV charger | Right to install | §20 WEG / §554 BGB (since 1 Dec 2020) | 🟢 Legal *right* — apartment community decides only the *how* |
| EV charger | Private parking | OSM tag + user checkbox | 🟢 Driveway/garage / 🟡 Street-only → public-charge fallback |
| EV charger | Grid registration | Hardcoded | ℹ️ ≤11 kW notify · >11 kW approval |
| Battery | Installation | Hardcoded | 🟢 Indoor, verfahrensfrei |
| Battery | Grid registration | Hardcoded | ℹ️ Register in MaStR within 1 month |

**GEG 2024 timeline (drives heat-pump urgency, *not* a block):** new heatings must be ≥65%
renewable. For *existing* buildings the duty couples to **municipal heat planning** — large
municipalities (>100 k) by **30 Jun 2026**, the rest by **30 Jun 2028**. Working boilers may keep
running and be repaired; constant-temperature boilers >30 years must be decommissioned (§72, with
owner-occupied exceptions).

**Data-source reality check (verified):**

- **Denkmalschutz has no single national API** (Länder competence). Bavaria's *DenkmalAtlas/
  BayernAtlas* is openly queryable (WFS); others vary. **Plan:** if the address is in a loaded
  Denkmal dataset → 🟡; else assume not listed + show a *"Is your home listed?"* checkbox. Demo uses a
  Bavarian address for the live API; checkbox is the national fallback.
- **MaStR has no clean count-by-PLZ REST** (Webdienst is SOAP + registration; only PLZ/Ort public).
  **Plan:** pre-load counts for the demo PLZs from the public **Gesamtdatenexport** into Supabase;
  elsewhere treat as ⚪ "unknown" (social proof only — never a gate).
- **OSM Overpass** (parking / building type) is free and already in the stack.

Layer-1 output feeds the engine as `roof_ok` + feasibility flags; it can *down-grade* an option
(street-only parking weakens the EV rung's PV-charging share) but in the common single-family case
everything is green.

---

## Layer 2 — Solar & battery (Electricity bucket)

**Primary roof model = PVGIS (free, no key). Google Solar = optional precision behind the proxy.**

```
# Sizing — from contract package tier, or roof geometry if known:
panels      = usable_roof_m2 / 1.95          # 1 modern module ≈ 1.95 m²
system_kwp  = panels × 0.44                  # ≈ 440 Wp / module (2026)
# Tier fallback (no geometry): SMALL≈6 · MEDIUM≈9 · LARGE≈12 kWp

# Annual yield — PVGIS PVcalc (live), constant fallback:
GET https://re.jrc.ec.europa.eu/api/v5_2/PVcalc
    ?lat=..&lon=..&peakpower=<kWp>&loss=14&mountingplace=building
    &angle=<tilt|35>&aspect=<azimuth|0>&outputformat=json
→ annual_yield_kwh = outputs.totals.fixed.E_y       # includes PR/losses
Fallback: annual_yield_kwh = system_kwp × 980        # DE avg (950–1050)

# Self-consumption, feed-in, arbitrage (load-aware — see note):
annual_consumption_kwh = household electricity + (HP electricity if rung ③) + (EV kWh if rung ④)
self_consumption_ratio = lookup(pv_vs_consumption, battery?)     # 30% PV-only · 60–65% +battery
self_consumed_kwh = min(annual_yield × self_consumption_ratio, annual_consumption_kwh)   # ← cap by load
exported_kwh      = annual_yield_kwh − self_consumed_kwh

elec_saving_self  = self_consumed_kwh × retail_price             # displaced grid import
elec_feedin_rev   = exported_kwh      × 0.0778                   # ✅ verified EEG ≤10 kWp
battery_arbitrage = usable_kWh × 300 cycles × 0.90 round_trip × 0.12 spread   # ✅ replaces "34%"

ELECTRICITY bucket €/mo = (elec_saving_self + elec_feedin_rev + battery_arbitrage) / 12
```

> **Load-aware cap (correctness):** self-consumption can never exceed actual consumption. A 9 kWp
> system on a 3,000 kWh/yr household is export-dominated until later rungs (HP, EV) add load — which
> is exactly why the **battery and PV become more valuable as you add options** (§5). No
> double-counting: PV charges the battery first (counts as self-consumption); only the *remaining*
> cycles are pure arbitrage, on their own line with a wider band. Arbitrage is credited **only** on
> the dynamic tariff (part of the bundle) — tying the battery to the tariff story Cloover asked for.

> Stretch: 8760-h sim = PVGIS `seriescalc` hourly × BDEW H0 profile, battery dispatched vs aWATTar.

---

## Layer 3 — Heat pump (Heating bucket)

**Primary = derive heat demand from *actual* fuel spend (most credible). Area method = fallback.**

```
# Heat demand from spend (primary):
#   OIL: 1 L ≈ 10.0 kWh gross × 0.85 boiler η = 8.5 kWh useful/L; oil ≈ €1.10/L
#   GAS: ≈ €0.115/kWh all-in × 0.90 η
heat_demand_kwh = (heating_eur_month × 12 / fuel_unit_price) × boiler_efficiency × calorific

# Area method (fallback, needs floor_area + building_year):
heat_load_W_m2 = lookup(building_year)         # §7: 150 (<1977) … 40 (>2016) W/m²
required_kW    = ceil_to(6/8/10/12/14/16, heat_load_W_m2 × floor_area_m2 / 1000)
heat_demand_kwh = required_kW × 1800           # full-load hours (DE single-family)

# Running cost & saving:
hp_electricity_kwh = heat_demand_kwh / SCOP            # SCOP 3.5 air-source (3.0–4.0)
solar_covered_kwh  = hp_electricity_kwh × overlap      # 0.15 PV-only · 0.30 +battery (winter-weak)
hp_grid_kwh        = hp_electricity_kwh − solar_covered_kwh
heating_new_cost   = hp_grid_kwh × retail_price / 12
HEATING bucket €/mo = heating_eur_month − heating_new_cost     # only if fuel ∈ {OIL, GAS}
```

> **Honest interaction:** a heat pump shifts load into winter when PV is weak, so PV helps heating
> *less* than mobility — the low `overlap` factor models this. Surfacing it is a credibility signal.

---

## Layer 4 — EV charger (Mobility bucket)

```
# ✅ CORRECTED — the original multiplied by consumption; it must divide.
litres_year   = mobility_eur_month × 12 / fuel_price_per_litre      # petrol €1.85, diesel €1.75
km_year       = litres_year / consumption_l_per_100km × 100        # ICE petrol ≈ 7.0 L/100km
ev_kwh_year   = km_year × ev_consumption_kwh_per_100km / 100        # EV ≈ 18 kWh/100km
ev_charge_cost = ev_kwh_year × blended_charge_price                 # ≈ €0.20/kWh
MOBILITY bucket €/mo = mobility_eur_month − ev_charge_cost / 12     # only if car ∈ {PETROL,DIESEL}
```

**Blended charge price ≈ €0.20/kWh** = PV surplus (≈ free, ~40%) + off-peak dynamic (~50%) +
occasional public DC (~10%). If Layer 1 found **street-only parking**, drop the PV share → blend rises
(~€0.30) and the saving shrinks honestly.

---

## 5. The incremental configurator — add options one at a time (Check24-style)

This is the heart of the product UX **and** the engine model. The four upgrades **stack**: each option
you add keeps everything below it and unlocks exactly one new value stream. Adding an option
recomputes the **single monthly number** and shows that option's own contribution — exactly the
Check24 "tick a box, the price updates" feel, but the number that updates is the *saving*.

### 5.1 The canonical ladder (the four steps)

```
START   →  + Solar / PV   →  + Battery   →  + Heat pump   →  + EV charger
  ∅          rung ①            rung ②          rung ③            rung ④
            SOLAR_ONLY       PV_BATTERY    PV_BATTERY_HEATPUMP   PV_BATTERY_HEATPUMP_EV   ← contract enum
```

Each rung carries **its own capex → its own subsidy → its own installment**, and is evaluated **on top
of the running state** (everything already ticked). So:

```
state₀ = baseline household (no upgrades)
for each option the user adds, in canonical order:
    stateₙ = stateₙ₋₁ + option
    Δ_gross(option)      = gross_saving(stateₙ)      − gross_saving(stateₙ₋₁)
    Δ_capex(option)      = capex_after_subsidy(option)            # this option's own capex
    Δ_installment(option)= annuity(Δ_capex, rate, term)
    Δ_net(option)        = Δ_gross(option) − Δ_installment(option)   # what THIS option adds to the saving
    cumulative_net       = Σ Δ_net   (= monthly_saving for the current selection — the North Star)
```

**Why marginal, in canonical order:** Δ_net values defined this way **sum exactly** to the headline
saving (no rounding drift, no double-counting), so every configurator row is honest — its "+€X/mo" is
literally the change in the one big number. This sequential attribution *is* the cumulative ladder.

### 5.2 The interaction that makes the ladder credible (not a sum of independents)

Later rungs **raise household electricity demand**, which **increases the value of the PV + battery
already installed** — more solar is self-consumed (the load cap in Layer 2 lifts), the battery cycles
more usefully, and flexible HP/EV load pairs with the dynamic tariff. The engine therefore recomputes
the **electricity bucket on the running state at every rung** — so e.g. the battery that looks
marginal at rung ② can turn clearly positive once rungs ③–④ add load. This is *why a bigger upgrade
can raise the monthly saving*, and it is the literal challenge answer.

### 5.3 Dependency & toggle rules (what the UI enforces)

| Option | Depends on | If toggled without dependency | Notes |
|---|---|---|---|
| ☀️ Solar/PV | — | — | The foundation; most rungs assume it. |
| 🔋 Battery | (recommended: PV) | allowed — battery still arbitrages grid on the dynamic tariff, but value is lower | UI nudges "add PV to unlock self-consumption". |
| ♨️ Heat pump | — | allowed (fossil→electricity saves on its own) | PV/battery boost it but aren't required. |
| 🚗 EV charger | — | allowed | PV surplus boosts it but isn't required. |

**Recommended product model = the strict nested ladder** (the 4 contract scenarios) because it matches
the challenge wording and the frozen contract, and the optimiser ranks exactly these. À-la-carte
(any subset of the 4) is physically meaningful and cheap to compute (≤16 evaluations of a pure,
sub-millisecond engine) — supported as the **stretch** "free configurator" mode (§9.1 note). For the
demo, present the ladder with independent toggle rows in canonical order.

### 5.4 The optimiser & up-sell

`recommend()` walks the ladder and returns the rung with the **largest `monthly_saving`** — *not*
necessarily the deepest (if the wallbox installment outweighs its fuel saving, rung ④ is skipped).
Up-sell is then a **diff** against the next-smaller rung, surfaced inline in the configurator:
*"Adding the heat pump turns €19/mo into €28/mo — because you're still burning oil at €180/mo."*

### 5.5 Financing overlay (the anchor)

```
capex_after_subsidy = capex − subsidies
   PV + battery:  0% VAT already (§12(3) UStG, since 2023) → no further federal grant assumed
   heat pump:     KfW 458 — 30% base + bonuses, capped 70% of eligible cost (cap €30,000 → max €21,000);
                  default modelled grant ≈ 50% (base 30% + Klima-bonus 20% if old boiler replaced)
   EV purchase:   €0 (Umweltbonus ended Dec 2023) — wallbox capex only
installment = annuity(capex_after_subsidy − downpayment, annual_rate, term_months)
              # contract defaults: term_months = 180, annual_rate = 0.05 (Cloover real APR TBC)
monthly_saving      = gross_saving − installment        # ← THE NORTH STAR (may be ≈0 early — honest)
saving_after_payoff = gross_saving                       # loan gone
break_even_month    = first month cumulative_net ≥ 0
```

### 5.6 Worked example (illustrative — engine produces exact figures)

Detached DE home, 3 people · €95 electricity · €180 oil · €160 petrol = **baseline €435/mo**.
PV MEDIUM 9 kWp · battery 8 kWh · air-source HP · wallbox. Financing 180 mo @ 5%. Note how the
electricity value *grows* as HP+EV add load (the interaction in §5.2):

| Step you add | + Capex (after subsidy) | + Installment | Δ gross /mo (on running state) | **Δ net /mo** | Cumul. net **now** | Cumul. after payoff |
|---|---:|---:|---:|---:|---:|---:|
| ☀️ + Solar/PV (9 kWp) | €13,050 (0% VAT) | €103 | +€122 | **+€19** | €19 | €122 |
| 🔋 + Battery (8 kWh) | €5,600 | €44 | +€24 | **−€20** | −€1 | €146 |
| ♨️ + Heat pump | €11,000 (€22k − 50% KfW) | €87 | +€116 | **+€29** | €28 | €262 |
| 🚗 + EV charger | €1,200 | €9 | +€67 | **+€58** | €86 | €329 |

Reading: solar alone is barely net-positive (export-dominated at low load). The battery is *negative
on its own* at step ②, but the household keeps it because steps ③–④ add the load that makes it pay —
the full bundle nets **≈ €86/mo from day one** and **≈ €329/mo after the loan is paid off**, break-even
at month ~150. The optimiser recommends the **full ladder** here (max net now). The Δ-net column is
literally what each configurator row shows the user. (All figures illustrative; the TDD'd engine and
live data produce the exact numbers.)

### 5.7 Confidence band

Each default carries an uncertainty; propagate to `±€Y` and name the biggest driver
("biggest uncertainty: your self-consumption ratio — add roof orientation to tighten it").
Sensitivity = re-run on ± shocks to the 3 riskiest inputs (irradiance, self-consumption, spot spread).

---

## 6. Dashboard (what the user sees) — a live configurator

- **YOUR SAVING: €X / month** — biggest text on the page, top centre; recomputes as options toggle.
- **The four option rows (Check24-style), in canonical order**, each a toggle showing its own
  contribution and capex:
  ```
  ☀️ Solar 9 kWp        +€19/mo    (€13,050 · 0% VAT)        [ ✓ ]
  🔋 Battery 8 kWh       −€20/mo    (€5,600)                  [ ✓ ]   ← honest: pays off once load grows
  ♨️ Heat pump           +€29/mo    (€22k − €11k KfW)         [ ✓ ]   ← "still on oil? this is €29/mo"
  🚗 EV charger          +€58/mo    (€1,200)                  [ ✓ ]
  ────────────────────────────────────────────────
  TOTAL  €86/mo now  →  €329/mo after payoff   ±€35
  ```
- **Honest curve:** *"≈ cost-neutral today → €329/mo once the loan is paid off"* + break-even year.
  This honesty is the trust-builder — lead the demo with it.
- Before vs after: *"Today €435/mo → with the Cloover bundle €Z/mo."*
- Permits panel: all green ✓ (Layer 1), with the one real flag (Denkmal/parking) if present.
- What you get free: smart meter, dynamic tariff, Cloover energy manager.
- Confidence chip `±€`. Assumptions drawer (every default labelled + editable → live re-run).
- **Claude paragraph** in plain German: 3 sentences on why *this* config fits *this* home.
- One green CTA: **Apply for Cloover financing**.

**90-sec demo flow:** type PLZ + 5 numbers → solar number appears → tick 🔋 (number dips, honest) →
tick ♨️ and 🚗 (number jumps, with the up-sell line) → edit one assumption → band tightens →
"Generate proposal" → installer copy appears.

---

## 7. Verified reference dataset (seed into Supabase — one source + fallback each)

> **Strategy:** pre-seed everything region-level so the demo runs offline; live PVGIS/aWATTar are a
> *toggle*, never a demo dependency. Mark every constant `verify@build` — refresh at setup.

| Constant | Value (2026) | Source | Fallback |
|---|---|---|---|
| Specific PV yield (DE) | live per lat/lon | PVGIS PVcalc | **980** kWh/kWp |
| Module | **0.44 kWp**, **1.95 m²** each | market 2026 | — |
| PV tiers | SMALL 6 / MED 9 / LARGE 12 kWp | contract `PvTier` | — |
| Battery tiers (usable) | STANDARD **8** / LARGE **12** kWh | contract `BatteryTier` | — |
| Self-consumption | 30% PV-only · **60–65%** +battery (capped by load) | BSW/HTW literature | 30 / 60% |
| Retail electricity | **€0.37**/kWh (refine per-PLZ grid fee) | BNetzA / Netztransparenz | €0.37 |
| **Feed-in (≤10 kWp)** | **€0.0778**/kWh (since 1 Feb 2026; → 0.0771 Aug) | [ADAC/EEG](https://www.adac.de/rund-ums-haus/energie/spartipps/einspeiseverguetung-pv-anlagen/) | €0.0778 |
| Dynamic-tariff spread (net) | **€0.12**/kWh | aWATTar day-ahead | €0.10 |
| Battery: cycles/yr · round-trip | **300** · **0.90** | engineering | — |
| Heating oil | **10.0** kWh/L · €**1.10**/L · η **0.85** | market | — |
| Gas | €**0.115**/kWh all-in · η **0.90** | market | — |
| Heat pump SCOP | **3.5** (3.0–4.0; DWD-HDD keyed = stretch) | manufacturer/JAZ | 3.5 |
| PV→HP overlap | 0.15 PV-only · 0.30 +battery | engineering | — |
| Heat-load by Baujahr (W/m²) | <1977 **150** · 77–94 **100** · 95–01 **80** · 02–08 **70** · 09–15 **55** · >2016 **40** | IWU/TABULA | 100 |
| Full-load hours (heating) | **1800** h | DE single-family | 1800 |
| Petrol / diesel | €**1.85** / €**1.75** per L | market | — |
| ICE / EV consumption | **7.0** L/100km · **18** kWh/100km | class default | — |
| EV blended charge | **€0.20**/kWh (PV+off-peak+public) | derived | €0.25 |
| Capex: PV | €**1,450**/kWp (small) → €1,300 (large) | market | €1,450 |
| Capex: battery | €**700**/kWh usable | market | €700 |
| Capex: heat pump (air, incl. install) | €**22,000** gross (range 18–30k) | market | €22,000 |
| Capex: wallbox | €**1,200** incl. install | market | €1,200 |
| **KfW 458 heat-pump grant** | 30% base, up to **70% / €21,000** (cap on €30k) | [ADAC/KfW](https://www.adac.de/rund-ums-haus/energie/spartipps/foerderung-heizung/) | 50% modelled |
| PV/battery VAT | **0%** (§12(3) UStG since 2023) | UStG | 0% |
| EV purchase grant | **€0** (Umweltbonus ended Dec 2023) | BAFA | €0 |
| Financing | term **180** mo, APR **5%** (Cloover real APR TBC) | contract defaults | — |

---

## 8. Data sources — endpoint, auth, limits, fallback

| Source | Endpoint / access | Auth | Tier | Fallback |
|---|---|---|---|---|
| **PVGIS** (yield, TMY) | `re.jrc.ec.europa.eu/api/v5_2/PVcalc`·`/seriescalc` | none | 🟢 | constant 980 |
| **aWATTar** (day-ahead) | `api.awattar.de/v1/marketdata` | none | 🟢 | seeded spread €0.12 |
| **Google Solar** (roof geometry) | `solar.googleapis.com/v1/buildingInsights:findClosest` | **key + billing**, EEA caveats (since 8 Jul 2025) | 🔵 optional, via FastAPI proxy | PVGIS + area heuristic |
| **OSM Overpass** (parking/building) | `overpass-api.de/api/interpreter` | none | 🟡 | user checkbox |
| **Denkmalschutz** | Länder WFS/INSPIRE (Bavaria live; others vary) | varies | 🟡 | user "listed?" checkbox |
| **MaStR** (neighbour count) | Gesamtdatenexport → seed Supabase (no count REST) | export | 🟡 | ⚪ "unknown" (social proof only) |
| **Grid fees per PLZ** | Netztransparenz.de / BNetzA CSV → seed | public | 🟡 | flat €0.37 retail |
| **KfW / EEG / GEG** | static verified constants (§7) | — | 🟢 | values in §7 |
| **Anthropic (Claude)** | via LLM adapter, server-side | **key (FastAPI only)** | 🟢 | OpenAI adapter |

> ⚠️ **Security:** Google Solar, Anthropic, and Supabase service-role keys exist **only** in FastAPI's
> environment. The Vite bundle ships **one** var: `VITE_API_BASE_URL`.

---

## 9. Contract & persistence

### 9.1 Engine endpoint (frozen — change only with `openapi.yaml`)

`POST /api/v1/advisor/recommend` → `Recommendation { best, alternatives[], upsell }`. The
**`alternatives[]` array is the four cumulative ladder steps** — each `ScenarioResult` carries
`breakdown {electricity,heating,mobility}_eur_month`, `installment_eur_month`, `monthly_saving_eur`
(North Star), `payback_note`. **The configurator's per-option "+€X/mo" = the difference between
consecutive `monthly_saving_eur` values** (§5.1) — the FE needs no extra call to render the toggles.

> **À-la-carte stretch:** to allow arbitrary subsets (battery without PV, HP-only…), extend the request
> with an optional `selection {pv,battery,heat_pump,ev}: bool` and return that bundle's result plus
> canonical-order marginals. Cheap (≤16 pure evaluations); keep the nested ladder as the default.

### 9.2 Enrichment endpoint (new — keeps the pure contract stable)

`POST /api/v1/advisor/site-check` → full address + optional `floor_area_m2`/`building_year` → runs
Layer 1 + roof geometry → `{ roof_ok, feasibility_flags[], energy_context, assumptions[] }`. The SPA
calls this first (richer mode), then `/recommend`. Form-only mode skips it and posts the bare
`Household`.

### 9.3 Supabase schema (minimal)

```
reference_plz   (plz PK, lat, lon, specific_yield, retail_price, grid_fee, climate_zone, mastr_count)
cache_pvgis     (lat, lon, tilt, azimuth, kwp, payload_json, fetched_at)        -- TTL 30d
cache_awattar   (market_area, day, payload_json, fetched_at)                    -- TTL 1d
advise_run      (id PK, household_json, options_json, recommendation_json, created_at)
proposal        (id PK, advise_run_id FK, copy_md, created_at)
denkmal_seed    (plz, geom/flag)   mastr_seed (plz, count)                      -- demo PLZs only
```

---

## 10. Risks & demo-safety

| Risk | Mitigation |
|---|---|
| Self-consumption ratio wrong → number not credible | defensible literature table (§7); load-cap; show band; cite in UI |
| Live API flaky in demo | seed reference data; PVGIS/aWATTar are a toggle; `?fixture` path |
| LLM hallucinates a number | LLM never computes; assert every figure in copy matches the payload |
| Over-claiming subsidies (esp. EV) | EV grant = €0; KfW capped 70%/€21k; cite sources |
| Configurator deltas don't sum to headline | canonical-order marginal attribution sums exactly (§5.1) |
| Denkmal/MaStR not national | user-confirm checkbox fallback; social-proof never gates |
| Secret leaks via Vite bundle | only `VITE_API_BASE_URL` client-side; all keys in FastAPI |
| Scope creep | MVP = Layers 1–5 nested ladder + KfW + LLM copy; hourly sim, Google Solar, à-la-carte are stretch |

---

## 11. Open decisions (carry into kickoff)

1. **Market scope:** lock to Germany (recommended — all data above is DE).
2. **Configurator mode:** nested ladder (MVP, matches contract + challenge) vs free à-la-carte subsets
   (stretch). Recommended: ladder for the demo, à-la-carte if green.
3. **Denkmal demo:** Bavaria address (live API) + national checkbox (recommended: both).
4. **KfW grant default:** 50% (base+Klima) vs conservative 30%. Recommended: 50%, editable assumption.
5. **Financing APR/tenor:** confirm Cloover's real product to replace the 5% / 180-mo contract default.
6. **Self-consumption fidelity:** heuristic table (MVP) vs 8760-h sim (stretch). Recommended: heuristic.
```
