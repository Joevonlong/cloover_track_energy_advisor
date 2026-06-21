# Customer Intelligence — Heimwende Energy Advisor

> Status: v0.1 · 2026-06-20
> Feeds into: system_workflow.md (intake layer, LLM advisor copy, subsidy engine)
> Core question: *who is this person, what data do we need from them, and how do we convince them?*

---

## 1. Why the person matters (not just the house)

The same house — 9 kWp PV, 8 kWh battery, air-source HP, wallbox — produces:
- a **€86/mo headline saving** for a cash-flow-stressed young family
- a **7.3% annual ROI** for a high-income investor
- a **+€35,000 property value uplift** for someone about to sell
- a **CO₂ offset of 4.2 t/yr** for an environmentalist

Same number, four different conversations. The LLM advisor must detect the profile and reframe accordingly.

---

## 2. Customer profile matrix

### 2.1 Profile signals to collect (add to Tier-1 intake)

| Signal | How to get it | Drives |
|---|---|---|
| **Ownership** | dropdown: owner / renter / landlord | gates whole upgrade path |
| **Home type** | detached / semi / apartment | roof potential, EV charger feasibility |
| **Building year** | year or decade | heat load, GEG obligation urgency |
| **Age of heating system** | years / decade | replacement subsidy eligibility |
| **Age of existing PV** | years (if any) | repowering scenario |
| **Household income bracket** | <€40k / €40–80k / >€80k (optional) | KfW income bonus (+30%) |
| **Planning to sell?** | yes / no / maybe in X years | real estate value angle |
| **Primary motivation** | save money / planet / independence / property | reframes the copy |
| **Risk appetite** | conservative / balanced / go big | financing tenor recommendation |

### 2.2 The four personas and how to sell each

#### A — Cash-flow family (35–45, mortgage, 2–3 kids)
- **Fear:** more monthly obligations, complexity, what if it breaks
- **What they hear:** "My mortgage is already €900/mo, I can't add more"
- **Selling angle:** *"This replaces costs you already pay — from month 1, your total outgoings drop"*
- **Lead with:** the monthly saving number, break-even month 0
- **Real estate:** secondary — mention it but don't lead
- **Subsidy:** emphasize KfW because it reduces the installment they're afraid of
- **Risk model:** show conservative (low) scenario first, then the expected

#### B — High-income professional (45–60, house paid off, >€8k/mo)
- **Fear:** scam, complexity, ugly roof, neighbour reaction
- **What they hear:** "This sounds like a lot of hassle for a few euros"
- **Selling angle:** *"Energy self-sufficiency. Your bills stop depending on OPEC or Russian gas. And your house is worth more."*
- **Lead with:** property value uplift + energy independence
- **ROI framing:** "Equivalent to a 7% p.a. guaranteed return on your capex, tax-free"
- **Don't lead with:** monthly saving (too small relative to income)
- **Subsidy:** still relevant (it's free money), but frame as "the state pays 50% of your heat pump"

#### C — Investor / landlord (any age, multiple properties)
- **Fear:** tenant disruption, capex, regulatory risk
- **What they hear:** "What's the IRR? What's my exit?"
- **Selling angle:** *"German EPC ratings now move property prices. A D-rated house in 2028 will be hard to sell or rent. A B-rated one commands +15%."*
- **Lead with:** property value + rental premium + GEG obligation as risk
- **ROI framing:** hard numbers — capex, subsidy, saving, payback, IRR
- **Subsidy:** landlord subsidy rules differ slightly — flag

#### D — Environmentalist / early adopter (any age, motivated by climate)
- **Fear:** greenwashing, doesn't trust corporate narratives
- **What they hear:** "Show me the actual CO₂ numbers"
- **Selling angle:** *"4.2 tonnes CO₂/yr offset. That's your car twice over. And you stop paying for Russian oil."*
- **Lead with:** CO₂ impact, self-sufficiency, technology story
- **Monthly saving:** secondary — they'll take it but it's not why they do it
- **Subsidy:** they want to know it's legitimate / not corrupted

#### E — Price-sensitive / low income (<€40k/yr household)
- **Fear:** can't afford it, will get into debt, sounds too good to be true
- **What they hear:** "I can't afford solar, that's for rich people"
- **Key insight:** This is the persona where the subsidy engine matters most
  - KfW 458: 30% base + 20% climate speed bonus + **30% income bonus = 80%, capped at 70%**
  - A low-income household replacing an oil boiler with a heat pump pays only 30% of capex
- **Selling angle:** *"The state pays 70% of your heat pump. Your monthly saving is bigger than the installment from day one."*
- **Lead with:** net positive from month 1, show the subsidy clearly
- **Rule:** only recommend an upgrade if `monthly_saving > 0` for this persona — never push someone into debt

---

## 3. Old equipment — replacement scenarios (currently missing)

This is where major savings and subsidies hide. The engine must detect and model these.

### 3.1 Old heat pump (>15–20 years old)

| Scenario | Old SCOP | New SCOP | Electricity saving | KfW eligibility |
|---|---|---|---|---|
| Replace old HP (15 yrs) | ~2.0 | 3.5 | **~40% less electricity** for same heat | ✅ KfW 458 if replacing with heat pump |
| Replace old HP (>20 yrs) | ~1.8 | 3.5 | **~50% less electricity** | ✅ KfW 458 + potentially Effizienzbonus |

**Key:** KfW 458 applies to *replacing a heat pump with a better heat pump*, not just replacing fossil heating. This is currently missing from the model.

**Heating saving for old HP replacement:**
```
old_hp_electricity = heat_demand_kwh / old_scop          # e.g. 15,000 / 2.0 = 7,500 kWh/yr
new_hp_electricity = heat_demand_kwh / new_scop          # e.g. 15,000 / 3.5 = 4,286 kWh/yr
saving_kwh = old_hp_electricity - new_hp_electricity     # 3,214 kWh/yr
HEATING bucket = saving_kwh × retail_price / 12          # ≈ €99/mo
```

**Intake:** ask "Do you already have a heat pump? How old?" → triggers this path.

### 3.2 Old solar PV (>15 years)

| Issue | Impact |
|---|---|
| Old panels degraded ~1%/yr → 15% less yield after 15 yrs | Understated production |
| Old inverters (SMA, Fronius gen 1) may fail or be incompatible with battery | Battery add-on blocked |
| EEG feed-in tariff for >20-yr-old systems: tariff expires | Grid feed-in may drop to 0 or market price |
| Old mono/poly panels: 280–320 Wp vs modern 440 Wp | Fewer kWp in same roof space |

**Repowering scenario:**
- Replace old panels + add battery → modern system produces 30–40% more
- KfW 442 covers battery addition to existing PV (owner-occupied residential)
- Some Länder have repowering grants (Bayern, BW)

**Intake:** ask "Do you already have solar? How old? System size?" → triggers repowering path.

### 3.3 Old boiler — GEG urgency (the closer)

GEG §72: **constant-temperature boilers >30 years must be decommissioned** (exceptions for owner-occupied single-family if owner lives in it before Feb 2002, but only until the house is sold/transferred).

This is not a block — it's a sales trigger:
- *"Your boiler is 32 years old. Under GEG §72 it needs to come out. You'll pay for a new one regardless — with KfW you pay 30% of a heat pump instead of 100% of a new boiler."*

### 3.4 Subsidy stacking — the full matrix (not flat 50%)

KfW 458 / BEG Heizungsförderung 2026:

| Bonus tier | % | Condition | Stackable? |
|---|---|---|---|
| Base (Grundförderung) | 30% | Any heat pump | Always |
| Effizienzbonus | +5% | Heat pump with high seasonal efficiency (A+++ or natural refrigerant) | Yes |
| Klimageschwindigkeitsbonus | +20% | Replacing oil/gas/coal boiler OR decommissioning under GEG obligation | Yes (until 2028, reducing after) |
| Einkommensbonus | +30% | Household income ≤ €40k/yr | Yes, mutually exclusive with some |
| **Maximum** | **70%** | Cap on €30k eligible cost → max grant **€21,000** | |

**The engine should compute the actual bonus tier, not use a flat 50%:**
```python
subsidy_pct = 0.30  # base
if hp_efficiency_class in ['A+++', 'natural_refrigerant']:
    subsidy_pct += 0.05
if heating_fuel in ['OIL', 'GAS', 'COAL'] or boiler_age > 30:
    subsidy_pct += 0.20
if household_income_eur_yr <= 40000:
    subsidy_pct += 0.30
subsidy_pct = min(subsidy_pct, 0.70)
grant_eur = min(capex_hp * subsidy_pct, 21000)
```

**Other subsidies not yet modelled:**

| Grant | What | Amount | Who |
|---|---|---|---|
| KfW 442 | Battery storage (owner-occupied) | up to 10% cost, varies | Homeowners adding battery |
| KfW 270 | Renewable energy standard loan | Low APR loan, not a grant | All |
| BAFA Heizungsförderung | Complements KfW 458 for consulting | up to €2,000 | All |
| Länder top-ups | Bayern: up to €3,000 additional; BW: BEW; NRW: progres.nrw | varies by state | PLZ-dependent |
| Municipal | Berlin Solar Atlas grants, Hamburg, Munich | varies | City-dependent |
| Grid operator | Some DSOs offer wallbox subsidies | €100–500 | PLZ-dependent |

---

## 4. Real estate value — the missing angle

For personas B (high income) and C (investor), property value uplift can be the primary sell.

### 4.1 What the evidence shows

| Upgrade | Value uplift | Source |
|---|---|---|
| EPC rating B vs D | +6–14% | empirica / IW Köln studies |
| Solar PV installed | +3–5% | HypZert / Knight Frank |
| Heat pump installed | +2–5% | market evidence |
| Full package (A rating) | +10–20% | composite estimate |
| No upgrade, post-GEG | −5–15% risk on D/E/F rated homes | forward risk |

**German-specific:** Energieausweis (EPC) is now disclosed at sale/rental. D/E/F-rated homes face growing buyer resistance and mortgage surcharges from banks (ECB green mortgage framework).

### 4.2 How to show it in the product

```
Property value uplift:
  Current estimated value: €450,000 (PLZ-based)
  EPC before: D (estimated from building year + heating fuel)
  EPC after upgrade: B (estimated)
  Uplift range: +€27,000 – €63,000 (6–14%)

  "Your energy upgrade pays for itself in home value alone —
   before counting a single euro of energy savings."
```

**Data source:** HypZert / Sprengnetter PLZ-level value estimates (free tier available). EPC class estimated from building year + heating + insulation standard (TABULA typology).

### 4.3 The "forced upgrade" future risk framing

Post-2026 GEG + EU EPBD (Energy Performance of Buildings Directive):
- EU requires worst-performing 15% of buildings upgraded by 2030
- German banks (KfW, ING-DiBa, etc.) are starting to factor EPC into mortgage rates
- An F-rated house in 2030 may be hard to insure and mortgage

*"This isn't optional in the long run. The question is whether you do it now with 70% subsidy, or later at full cost."*

---

## 5. Financing rationale — why finance, not pay cash?

Many customers instinctively want to pay cash. Here's why financing often wins:

| Argument | Explanation |
|---|---|
| **Positive cashflow from day 1** | If monthly saving > installment, you're ahead immediately — you'd lose that cashflow gap by paying cash upfront |
| **KfW APR vs alternative** | KfW 270 / 124 loans at ~3–4% APR. If you can earn >4% elsewhere (index fund, rental), financing wins |
| **Subsidy before financing** | Grant is applied to capex first, reducing the loan principal — so you finance only 30% of a heat pump |
| **Inflation hedge** | Fixed installment, rising energy costs → real cost of installment falls over time |
| **Liquidity** | Keep €40k liquid for emergencies vs locking it in your roof |
| **Tax (business owners / landlords)** | Loan interest may be deductible; direct capex less so |

**The Cloover bundle advantage:**
- Cloover earns margin on the dynamic tariff → can offer below-market APR on the loan
- This is the structural moat: banks can't bundle tariff revenue into loan pricing
- Frame it: *"Cloover's financing is cheaper because they earn on your tariff, not just your interest"*

### 5.1 Financing decision tree in the product

```
Is monthly_saving > installment from day 1?
  YES → "Finance it. You make money from month 1."
  NO  → show break-even month honestly
        if break_even_month < 36: "Near-neutral now, then €X/mo — typical for full upgrades"
        if break_even_month > 60: flag it, only recommend if after-payoff saving is strong

Can the household qualify for KfW?
  YES → show KfW APR as default
  NO  → show Cloover private financing

Does the customer have >€50k liquid?
  If they input high income and no mortgage → surface "cash vs finance" comparison
```

---

## 6. The "best case scenario" engine (what the LLM builds toward)

The LLM advisor should construct the *best possible credible case* for this specific person:

```
Given:
- Profile: 58-yr old homeowner, oil heating (boiler 28 yrs old), petrol car, income €65k/yr, PLZ 80333 (Munich)
- Existing: no PV, no battery

Best case output:
1. Heat pump NOW (GEG urgency + KfW 458: 30%+20%=50% → grant €11k on €22k)
2. PV 9 kWp + battery 8 kWh (KfW 270 loan, 0% VAT)
3. Wallbox (park in own garage ✅)
4. Upgrade EPC from E → B → Munich property value +€45k–€90k

Financing: €23,800 after subsidies · 180 mo @ 4.5% → €182/mo installment
Gross saving: €267/mo
Net saving now: €85/mo
Net saving after payoff: €267/mo
Break-even: month 0 (positive from day 1)

LLM copy (for Munich homeowner, B persona):
"Your boiler is approaching GEG decommissioning age — and Munich property buyers now 
ask for the Energieausweis on day one. This upgrade takes your home from E to B, adds 
an estimated €55,000–90,000 to its market value, and saves you €85/month while the loan 
runs. Once it's paid off: €267/month, permanently. The state covers half the heat pump. 
Cloover handles the rest in one package."
```

---

## 7. What the intake needs to add (to support all of the above)

Currently missing from Tier-0/Tier-1:

| New field | Why | Where |
|---|---|---|
| `building_year` | GEG obligation check, heat load, EPC estimation | Tier-0 (add it) |
| `heating_system_age` | Old HP path, boiler decommissioning urgency | Tier-1 |
| `existing_pv_age` | Repowering scenario | Tier-1 |
| `existing_pv_kwp` | How much to add | Tier-1 |
| `household_income_bracket` | KfW income bonus (+30%) | Tier-1 (optional, sensitive) |
| `primary_motivation` | Reframes LLM copy | Tier-1 (dropdown) |
| `planning_to_sell` | Real estate angle | Tier-1 |
| `property_value_estimate` | Real estate uplift calculation | Tier-1 or PLZ-derived |
| `ownership` | owner / renter / landlord | Tier-0 (add it) |

---

## 8. Data sources to add

| Data | Source | Use |
|---|---|---|
| KfW 458 bonus tiers | KfW.de (static, verify quarterly) | Correct subsidy calc |
| KfW 442 battery grant | KfW.de | Battery-only or add-on |
| Länder top-ups | Each Länder energy agency (static seed, PLZ-keyed) | Stacking |
| Property value by PLZ | Sprengnetter / empirica (API or static seed) | Real estate uplift |
| TABULA typology | IWU TABULA DE dataset | EPC class estimation from year + type |
| EPC uplift studies | empirica / IW Köln (static reference) | Value uplift table |
| Boiler age → SCOP lookup | Engineering (static) | Old HP replacement saving |
