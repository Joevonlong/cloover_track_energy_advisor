# Heimwende Energy Advisor — Master Brainstorm & Build Plan

> Cloover track · {Tech: Europe} Energy × AI Hackathon · Berlin 2026-06-20
> Status: **living document — v0.1**. We iterate on this together.
> Deadline: **Sun 2026-06-21, 14:00**. Optimise for a *credible, demoable* saving number.

---

## 0. The one thing to remember

We sell **one product** (upgrade + financing + dynamic tariff) and show **one number**:

```
monthly_saving = current_monthly_spend − (loan_installment + new_monthly_energy_cost)
```

Everything below exists to make that number **credible**, **honest over time**, and
**explained in plain language an installer can paste into a proposal**.

If a feature does not move, defend, or explain that number, it is out of scope for the demo.

---

## 1. Product framing (why this wins the track)

The judge-facing story Cloover asked for: *today, financing is sold first and the tariff is
bolted on afterwards — that's backwards.* We invert it:

1. **Outcome first.** "You save **€X/month**." Not "here's a 9.6 kWp system."
2. **Honest about the curve.** If the installment eats the saving early, we say so:
   *"≈ cost-neutral today, then €X/month once the loan is paid off."* This honesty is a
   differentiator, not a weakness.
3. **One checkout.** Upgrade + loan + tariff presented as a single monthly figure.
4. **The AI earns its place** by (a) turning *minimal* input into a full model, (b) **choosing
   the upgrade path that maximises the saving**, and (c) **writing the proposal copy**.

---

## 2. User input — minimal in, rich model out

Design principle: **progressive disclosure**. Ask the 6 things we truly need, derive the rest,
let power users refine. Two entry modes share the same schema:

- **Form mode** (React Hook Form + Zod) — fast, deterministic, demo-safe.
- **Conversational mode** (LLM intake) — "Tell me about your home" → LLM extracts the schema,
  asks one follow-up at most. Great for the wow-factor; keep form as the fallback.

### 2.1 Tier 0 — the absolute minimum (the "from minimal inputs" promise)

| # | Input | Example | Why we need it |
|---|-------|---------|----------------|
| 1 | **Postal code (PLZ)** | 10115 | Unlocks irradiance, grid fees, climate, prices |
| 2 | **Home type / ownership** | detached house, owner | Roof potential, eligibility for subsidies |
| 3 | **Current electricity spend** | €95/mo | Baseline bucket 1 |
| 4 | **Heating fuel + spend** | oil, €180/mo | Baseline bucket 2 + heat-pump upside |
| 5 | **Car type + spend** | petrol, €160/mo | Baseline bucket 3 + EV upside |
| 6 | **Rough household size** | 3 people | Load profile, consumption scaling |

That is enough to produce a first saving number. Everything else has a **smart default keyed off
PLZ + home type** (see §4) and is optional.

### 2.2 Tier 1 — optional refinements (improve certainty, shown as "make this more accurate")

Roof orientation & tilt · usable roof area / annual PV yield · annual driving distance (km) ·
year built / insulation standard · existing PV or battery · planned occupancy changes ·
preferred loan tenor · appetite for upfront payment.

### 2.3 Input UX rules

- Every Tier-1 field we *don't* have is filled by a labelled assumption ("assumed south-facing,
  35° tilt"). The user can override; overrides visibly tighten the confidence band.
- Money inputs are **whole EUR/month** (matches the OpenAPI contract). Engine converts to annual
  internally.
- Never block the result on missing data — degrade to defaults and flag uncertainty.

---

## 3. The savings model — how we make the number credible

This is the heart of the project and the **pure, TDD'd domain core** (`apps/api/src/app/domain/`,
zero I/O). Three buckets, one optimiser, one financing overlay.

### 3.1 Baseline (today)

```
current_monthly_spend = electricity_spend + heating_spend + mobility_spend
```

We also reconstruct *physical* baselines (kWh/year electricity, kWh/year heat demand, km/year and
fuel litres) from spend ÷ local unit price, so the upgrade math is energy-based, not just €-scaled.

### 3.2 Bucket 1 — Electricity (solar self-consumption + battery arbitrage)

```
pv_yield_kwh       = kWp × specific_yield(PLZ)            # PVGIS, ~950–1050 kWh/kWp in DE
self_consumed_kwh  = pv_yield_kwh × self_consumption_ratio(load, battery)
exported_kwh       = pv_yield_kwh − self_consumed_kwh
electricity_savings = self_consumed_kwh × retail_price
                    + exported_kwh × feed_in_tariff
                    + battery_arbitrage(dynamic_tariff)   # charge cheap, discharge expensive
new_grid_import_cost = (annual_consumption − self_consumed_kwh) × effective_tariff
```

- **Self-consumption ratio** is the make-or-break variable. Two fidelity levels:
  - *Heuristic (MVP):* lookup table by (PV size vs consumption, battery yes/no) — e.g. ~30% PV-only,
    ~60–70% with battery. Fast, defensible, good enough to demo.
  - *Hourly sim (stretch):* 8760-hour simulation = PVGIS hourly profile × BDEW H0 load profile,
    battery dispatched against aWATTar day-ahead prices. This is the "wow, it's real" upgrade.
- **Battery arbitrage** = Σ over days of (discharge at peak price − charge at trough price) × usable
  capacity × round-trip efficiency × cycles. Only meaningful with a dynamic tariff — ties the
  battery to the tariff story.
- **Two ladder rungs, no double-counting:** rung ① (PV) earns the self-consumption layer; rung ②
  (battery) earns *extra* self-consumption (midday→evening shift) **plus** grid arbitrage. Allocate
  PV charging to self-consumption first; only the remaining battery cycles count as pure arbitrage.
  Keep arbitrage on its own line with its own (wider) confidence band — its value swings with the
  spot spread.

### 3.3 Bucket 2 — Heating (fossil → heat pump)

```
heat_demand_kwh   = heating_spend / fuel_unit_price          # litres/m³ → kWh via calorific value
hp_electricity    = heat_demand_kwh / SCOP(PLZ_climate)      # SCOP ≈ 3.0–4.0
heating_new_cost  = hp_electricity × effective_tariff (− extra self-consumption if PV)
heating_savings   = heating_spend − heating_new_cost
```

- SCOP keyed to local climate (DWD heating-degree-days). Air-source default; note radiator vs
  underfloor caveat in the explanation.
- Heat pump shifts load into winter when PV is weak → models the *interaction* honestly (PV helps
  heating less than mobility). Good credibility signal for judges.

### 3.4 Bucket 3 — Mobility (petrol/diesel → EV)

```
km_year         = mobility_spend / fuel_price × consumption_l_per_100km   # back out distance
ev_kwh          = km_year × ev_consumption(kWh/100km) / 100
ev_charging_cost = ev_kwh × charging_price (off-peak dynamic / PV surplus blend)
mobility_savings = mobility_spend − ev_charging_cost
```

- Charging price is a **blend**: PV surplus (≈ free), off-peak dynamic tariff, occasional public
  charging. The off-peak + PV blend is where the saving comes from — again ties back to the tariff.

### 3.5 The upgrade ladder — cumulative, not a menu (the "picks the strongest path" core)

The four upgrades **stack**: each rung keeps everything below it and unlocks exactly one new value
stream. We model them as an incremental ladder, not four independent configurations.

| Rung | Adds | Unlocks value stream | Bucket | Δ net/mo | Cumulative net/mo |
|------|------|----------------------|--------|---------:|------------------:|
| ① | Solar / PV | self-consumption of own generation | Electricity (a) | +€38 | €38 |
| ② | + Battery | ↑ self-consumption + dynamic-tariff arbitrage | Electricity (b) | +€23 | €61 |
| ③ | + Heat pump | fossil heating → (partly self-generated) electricity | Heating | +€55 | €116 |
| ④ | + EV charger | petrol → off-peak / PV charging | Mobility | +€26 | €142 |

Each rung carries its **own capex → own installment**, so a rung's incremental net saving =
its incremental gross saving − its incremental installment. **The optimiser walks the ladder and
stops at the depth that maximises cumulative net saving** — it does *not* assume deeper is always
better (if, say, the EV installment outweighs its fuel saving, rung ④ is skipped). This is the
literal challenge answer: *the configuration that lands the biggest monthly saving.*

**Why cumulative ≠ sum of independents (the credibility point):** later rungs raise household
electricity demand, which **increases the value of the PV + battery already installed** — more
solar is self-consumed, the battery cycles more usefully, and flexible EV / heat-pump load pairs
with the dynamic tariff. The engine therefore computes each rung **on top of the running state**,
never in isolation. This interaction is exactly why a bigger upgrade can *raise* the monthly saving.

### 3.6 Financing overlay (the anchor)

```
capex_after_subsidy = capex − subsidies            # KfW 458 heat pump up to 70% / €21k cap, etc.
loan_installment    = annuity(capex_after_subsidy − downpayment, apr, tenor_months)
net_saving_now      = gross_saving − loan_installment
net_saving_after_payoff = gross_saving            # loan gone
```

Output is a **two-phase honest number**: `net_saving_now` (may be ≈0 or slightly negative early)
and `net_saving_after_payoff`, plus the **break-even month**.

### 3.7 Certainty / confidence (the "savings certainty" requirement)

Don't print false precision. Each input default carries an uncertainty; propagate to a **band**:
show `€X/mo (±€Y)` and a one-line driver ("biggest uncertainty: your self-consumption ratio —
add roof orientation to tighten it"). Sensitivity = re-run engine on ± shocks to the 3 riskiest
inputs (irradiance, self-consumption, future spot spread).

### 3.8 Up-sell logic (built into the optimiser, not bolted on)

The optimiser already compares scenarios, so up-sell is a *diff*: "You asked about solar. Adding a
heat pump turns your €40/mo into €115/mo because you're still burning oil at €180/mo." Always
framed back to the financed monthly saving. Trigger heuristics: oil/gas heating present →
heat-pump nudge; petrol car + high mileage → EV nudge; high daytime export → battery nudge.

---

## 4. Datasets the system needs (detailed)

Legend — **Tier**: 🟢 must-have for a credible demo · 🟡 improves accuracy · 🔵 stretch.
For the hackathon, **pre-fetch and cache** the slow/region-level data; only per-household math is live.

### 4.1 Solar / irradiance
| Data | Source | Granularity | Access | Use | Fallback |
|------|--------|-------------|--------|-----|----------|
| 🟢 Specific PV yield (kWh/kWp) | **PVGIS (EU JRC)** PVcalc API | per lat/lon, monthly | Free, no key | PV production from kWp | Constant 950 kWh/kWp (DE avg) |
| 🟡 Hourly PV profile (TMY) | **PVGIS** seriescalc / TMY | 8760 h | Free | Self-consumption sim | Monthly profile shape |
| 🟡 Roof geometry/area | user input / OSM / Google Solar API | per address | manual / API | Max kWp | Default by home type |

### 4.2 Electricity prices & tariff
| Data | Source | Granularity | Access | Use |
|------|--------|-------------|--------|-----|
| 🟢 Day-ahead spot price | **aWATTar API** (DE/AT, free), ENTSO-E Transparency, EPEX | hourly | free / key | Dynamic tariff, battery & EV arbitrage |
| 🟢 Retail price components | Stromsteuer, EEG/levies, Konzessionsabgabe, supplier margin | static table | public | Build effective retail €/kWh |
| 🟢 Grid fees by region | **Netztransparenz.de**, BNetzA, BDEW; per-DSO/PLZ | per PLZ/DSO | public CSV | Zip-level price accuracy (the bonus ask) |
| 🟢 Feed-in tariff (Einspeisevergütung) | EEG current rate (~7–8 ct/kWh) | static | public | Value of exported PV |

### 4.3 Heating
| Data | Source | Use |
|------|--------|-----|
| 🟢 Fuel unit prices (gas ct/kWh, heating oil €/l) | public market / monthly index | Convert spend → kWh heat demand |
| 🟢 Calorific values & boiler efficiency | engineering constants | Litres/m³ → kWh |
| 🟢 SCOP by climate | manufacturer SCOP + DWD heating-degree-days | Heat → electricity |
| 🟡 Building heat demand benchmark (kWh/m²·a by Baujahr) | IWU/TABULA typology | Sanity-check / fill missing spend |

### 4.4 Mobility
| Data | Source | Use |
|------|--------|-----|
| 🟢 Petrol/diesel price (€/l) | public market | Back out km/year |
| 🟢 ICE consumption (l/100km) & EV consumption (kWh/100km) | class-based defaults | Energy swap |
| 🟡 Annual mileage | user input | Tighten mobility bucket |

### 4.5 Subsidies & financing
| Data | Source | Use |
|------|--------|-----|
| 🟢 Heat-pump grant | **KfW 458 / BEG Heizungsförderung** — 30% base, up to **70% / €21k cap** (2026) | Reduce heat-pump capex |
| 🟡 PV/battery & regional grants | KfW, Länder/municipal programmes | Reduce capex |
| 🟢 Loan terms (APR, tenor) | **Cloover financing product** | Annuity → installment |
| ⚠️ EV purchase grant | Umweltbonus *ended Dec 2023* — model **€0** unless a 2026 scheme is confirmed | Avoid overstating |

### 4.6 Equipment cost benchmarks (CAPEX)
| Item | Benchmark (DE, rough) | Use |
|------|----------------------|-----|
| 🟢 PV | ~€1,300–1,600 /kWp installed | Capex |
| 🟢 Battery | ~€600–900 /kWh usable | Capex |
| 🟢 Heat pump (air-source, incl. install) | ~€20–35k before subsidy | Capex |
| 🟢 EV charger (wallbox) | ~€800–1,500 | Capex |
| 🟡 EV vehicle premium | model as separate decision | Optional |

### 4.7 Load profiles
| Data | Source | Use |
|------|--------|-----|
| 🟡 Standard household load profile | **BDEW H0** | Hourly self-consumption sim |
| 🔵 Real smart-meter profile | user CSV upload | High-fidelity mode |

> **Hackathon data strategy:** seed a single JSON/SQLite "reference dataset" (a few representative
> PLZ regions with their grid fees, irradiance, climate, prices) so the demo runs offline and fast.
> Live API calls (PVGIS, aWATTar) are a **nice-to-have toggle**, not a demo dependency.

---

## 5. System design

### 5.1 Pipeline (left to right)

```
            ┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐
 minimal →  │  INTAKE     │ → │  RESOLVER    │ → │  SAVINGS       │ → │  OPTIMISER   │
 input      │ form / LLM  │   │ enrich from  │   │  ENGINE        │   │ pick max net │
            │ → schema    │   │ datasets §4  │   │ (pure domain)  │   │ saving       │
            └─────────────┘   └──────────────┘   └───────────────┘   └──────┬───────┘
                                                                            ↓
                                              ┌──────────────┐   ┌──────────────────┐
                                  results ←   │  ADVISOR     │ ← │  SCENARIO RESULTS │
                                  + proposal  │ LLM explains │   │ + confidence band │
                                              └──────────────┘   └──────────────────┘
```

### 5.2 Component responsibilities (respecting `CLAUDE.md`)

- **Intake** (`apps/web` + `apps/api` adapter): collect/parse inputs into the OpenAPI request
  schema. LLM intake lives behind the LLM adapter; produces the *same* schema as the form.
- **Resolver** (`adapters/`): turn Tier-0 input + PLZ into a fully-populated model by joining the
  reference datasets (§4). Pure functions where possible; I/O isolated in adapters.
- **Savings Engine** (`domain/` — **pure, TDD, zero I/O**): the math in §3. Deterministic,
  fast, unit-tested. *This is where the credibility lives.*
- **Optimiser** (`domain/`): enumerate scenarios, return the max-net-saving config + ranked list.
- **Advisor** (`adapters/llm`): the LLM **explains and sells — it does not compute**. It receives
  the engine's structured output and writes (a) the headline rationale, (b) the up-sell nudge,
  (c) installer-ready proposal copy. Keeping math out of the LLM is what makes the number trustworthy.
- **Results API** (`apps/api`): one endpoint returns the chosen scenario, the full comparison,
  the financing curve, the confidence band, and the generated copy.

### 5.3 Key design decisions

- **LLM computes nothing.** It narrates structured numbers. (Trust + determinism + testability.)
- **Contract-first.** `specs/api/openapi.yaml` is the seam; FE codes against the generated client.
- **Caching.** Region-level data pre-fetched into Supabase/SQLite; per-request math is in-memory.
- **Determinism for demo.** A `?seed`/fixture path so the live demo can't be broken by a flaky API.
- **Provider-agnostic LLM adapter** (Claude default) — already in the stack.

### 5.4 Suggested API shape (sketch — formalise in OpenAPI)

`POST /api/advise`
```jsonc
// request (Tier-0 + optional Tier-1)
{ "plz": "10115", "homeType": "detached", "occupants": 3,
  "spend": { "electricity": 95, "heating": 180, "mobility": 160 },
  "heatingFuel": "oil", "carType": "petrol",
  "options": { "loanTenorMonths": 120 } }

// response
{ "recommended": "S4",
  "headlineSavingPerMonth": 142, "confidence": { "low": 105, "high": 175 },
  "breakEvenMonth": 0, "savingAfterPayoffPerMonth": 268,
  "buckets": { "electricity": 61, "heating": 55, "mobility": 26 },
  "financing": { "capex": 41000, "subsidies": 14000, "installment": 173, "apr": 5.9, "tenorMonths": 120 },
  "scenarios": [ /* S0..S4 each with net saving for the comparison view */ ],
  "explanation": "…LLM prose…",
  "proposalCopy": "…installer paste-in…",
  "assumptions": [ {"field":"tilt","value":"35°","source":"default"} ] }
```

---

## 6. Presentation / product UX (what the user sees)

The screen must make the **one number unmissable** and the honesty unmistakable.

1. **Hero — the number.** Huge: **"You save €142 / month."** Sub-line with the honest curve:
   *"≈ cost-neutral today → €268/month once your 10-year loan is paid off."* Confidence chip: `±€35`.
2. **The honest timeline chart.** X = months; two areas: *while financing* vs *after payoff*; mark
   the break-even month. This single chart is the trust-builder — lead the demo with it.
3. **Bucket breakdown.** Three tiles: Electricity €61 · Heating €55 · Mobility €26 — each expandable
   to "why" (self-consumption %, SCOP, off-peak charging).
4. **Scenario comparison.** Cards S1→S4 with net €/mo; the recommended one highlighted; a clear
   *"why not just solar?"* answer (the up-sell, quantified).
5. **Up-sell nudge.** Inline: "Still on oil? The heat pump is doing €55/mo of your saving."
6. **Assumptions drawer.** Every default labelled + editable; editing re-runs and tightens the band
   live. Demonstrates rigour.
7. **Installer proposal export.** One button → LLM-written, paste-ready proposal text (+ PDF
   stretch). This is the literal deliverable the challenge names.

**Demo flow (90 sec):** type a PLZ + 5 numbers → big saving appears → toggle "add heat pump" →
number jumps → open assumptions, change one → band tightens → click "Generate proposal" → copy appears.

---

## 7. Pitch / judging presentation (for the team, separate from the app)

Suggested 5-slide arc:

1. **The inversion.** "Financing-first is backwards. We sell the outcome: one monthly number."
2. **The North Star.** The formula + the honest two-phase curve. (Credibility up front.)
3. **Live demo.** Minimal input → biggest-saving config → proposal copy. (The bulk of the time.)
4. **How the number is credible.** Pure deterministic engine + real DE data (PVGIS, day-ahead
   spot, KfW subsidies, zip-level grid fees) + LLM explains, never computes.
5. **The up-sell wedge + business fit for Cloover.** Bigger upgrade → bigger saving → more financed
   volume, sold honestly. Roadmap line.

Keep slides sparse; let the working product carry it. Judges reward a *credible* number over a
flashy one.

---

## 8. What we need to achieve the goal (build plan to Sun 14:00)

### 8.1 MVP cut (must work in the demo)
- Tier-0 form → `/api/advise` → headline saving + honest curve + 3 buckets.
- Heuristic self-consumption (no hourly sim needed for v1).
- Scenarios S1–S4 + optimiser pick.
- Financing annuity + KfW heat-pump subsidy.
- LLM explanation + proposal copy.
- One reference PLZ dataset seeded (offline-safe).

### 8.2 Stretch (only if MVP is green)
- 8760-hour self-consumption + battery arbitrage sim.
- Live PVGIS + aWATTar toggle.
- Zip-level grid fee join for 2–3 regions.
- Conversational LLM intake.
- PDF proposal export.

### 8.3 Parallel work split (contract-first lets us not block each other)
- **Person A — Domain/engine (Python, TDD):** §3 math + optimiser + tests. Owns credibility.
- **Person B — Data/adapters:** §4 reference dataset + resolver + (stretch) live APIs.
- **Person C — Frontend:** §6 screens against the generated client + mock fixtures from day one.
- **Person D — LLM advisor + pitch:** prompt for explanation/proposal + slides + demo script.

First 2 hours: **freeze `openapi.yaml`** (the §5.4 shape) so all four can run in parallel.

### 8.4 Top risks & de-risking
| Risk | Mitigation |
|------|-----------|
| Self-consumption ratio wrong → number not credible | Use defensible literature table; show band; cite source in UI |
| Live API flakiness in demo | Seed offline reference dataset; APIs are a toggle |
| LLM hallucinates numbers | LLM never computes; it only formats engine output; assert numbers in copy match payload |
| Over-claiming subsidies (esp. EV) | Model EV grant = €0 (Umweltbonus ended 2023); cite KfW for heat pump |
| Scope creep | This doc's MVP cut is the line; stretch only when green |

---

## 9. Open questions — let's decide these next

1. **Market scope:** lock to **Germany** (Heimwende, oil/gas heating, DE subsidies) for the demo? (Recommended.)
2. **EV scope:** model EV as *charging-cost swap only* (ignore vehicle purchase price), or include the car capex? Big effect on the number.
3. **Self-consumption fidelity for v1:** heuristic table (safe) vs hourly sim (impressive)? Recommend heuristic for MVP, sim as stretch.
4. **Tariff:** assume the household *switches to the dynamic tariff* as part of the product (so battery/EV arbitrage counts), or keep a flat-tariff baseline option to compare?
5. **Confidence band:** show it (honest, on-brand) or hide it for a cleaner hero number? Recommend show, small.
6. **Proposal output:** copy-to-clipboard text only for v1, or also a styled PDF?

---

### Appendix A — Worked example (sanity check, illustrative numbers)

Detached DE home, 3 people, oil heat, petrol car. Today: €95 elec + €180 heat + €160 fuel =
**€435/mo**. Full upgrade (9 kWp PV + 8 kWh battery + air-source HP + wallbox), capex ~€41k,
~€14k KfW subsidy, €27k financed over 120 mo @ 5.9% ≈ **€173/mo** installment. New energy cost
~€120/mo. → **gross saving ≈ €315**, **net now ≈ €142/mo**, **≈ €315/mo after payoff**. (Numbers
to be replaced by the engine — here only to validate the shape of the model.)

---

*Sources for the data anchors used above: PVGIS (EU JRC); aWATTar/Tibber day-ahead APIs;
KfW 458 / BEG Heizungsförderung (2026: 30% base, up to 70% / €21k cap). Replace placeholder
prices with seeded current values before the demo.*
