# Solar Layer — How It Works

## Overview

Layer 1 answers one question: **given a house address, how much money can solar panels save this household per month?**

Input: a house address (street, city, postcode) + basic household data.  
Output: optimal system size, annual yield, monthly savings, capex, confidence band.

---

## Files

| File | Purpose |
|---|---|
| `google_solar.py` | **Step 1–2: Address → real roof data via Google APIs** |
| `pipeline.py` | **Step 3–9: Sizing + physics + offer generation engine** |
| `physics.py` | Clean re-exports from pipeline.py — typed public surface |
| `economics.py` | Feed-in tariffs, capex formula, VAT |
| `__init__.py` | Package exports |
| `test_pipeline.py` | Test suite: physics bounds, sizing ranges, backtest |
| `merged_input_output.csv` | 1,062 real DE installer projects for backtest |

---

## Step-by-step pipeline

### Step 1 — Geocoding (`google_solar.py → geocode()`)
```
address string  →  Google Geocoding API  →  lat, lng
```

### Step 2 — Roof geometry + local irradiance (`google_solar.py → roof_from_address()`)
```
lat, lng  →  Google Solar buildingInsights endpoint  →  RoofData:
    max_modules                 ← panels that fit on south-facing segments only
    usable_area_m2              ← sum of south-facing roof segments (azimuth 90–270°)
    dominant_orientation        ← "S" | "SE" | "SW" | "E" | "W" | "N"
    specific_yield_kwh_per_kwp  ← real local irradiance from satellite data
    source                      ← "google_solar" | "floor_area_fallback"
```

**Why south-facing only?**  
Google returns ALL roof segments. North/NE/NW faces are excluded — only segments
with azimuth 90–270° (east to west through south) are counted as viable.

**Why satellite irradiance matters:**  
Google Solar measures actual sunshine at your exact location from satellite imagery.
This is more accurate than any regional average:

| Location | Typical yield |
|---|---|
| Munich / Bavaria | ~1,100 kWh/kWp/yr |
| Baden-Württemberg | ~1,000–1,050 kWh/kWp/yr |
| Frankfurt | ~1,000 kWh/kWp/yr |
| Berlin | ~950 kWh/kWp/yr |
| Hamburg | ~900 kWh/kWp/yr |

Example: Am Nahholz 55, Buchen → **1,034 kWh/kWp/yr** (SE roof, real satellite data).

**Fallback** when Google Solar has no coverage:
```
usable_area_m2 = floor_area_m2 × 0.30
orientation    = "S"
specific_yield = 950 kWh/kWp/yr  (Germany average)
source         = "floor_area_fallback"
```

---

### Step 3 — Optimal system sizing (`pipeline.py → generate_candidates()`)
The pipeline does NOT just install the maximum number of panels.
It tries **every sensible module count** from ~5 kWp up to the roof cap in steps,
then lets the scoring pick the optimal size:

```
min_modules = ~5 kWp worth of panels
step        = roof_cap / 20  (up to 20 different sizes)
module_range = [min, min+step, ..., roof_cap]
```

All sizes × all battery options × all brands are simulated. The best combination
per offer type (Budget / Balanced / Max Independence) wins.

---

### Step 4 — Annual yield (`pipeline.py → simulate_energy()`)
```
system_kwp × specific_yield × ORIENTATION_FACTOR[orientation] = annual_yield_kwh
```

**ORIENTATION_FACTOR** (HTW Berlin / real installer data):
```
S → 1.00 | SE/SW → 0.95 | E/W → 0.85 | N → 0.60
```

The orientation factor corrects for roof direction on top of Google's local irradiance.
Example: SE roof at 1,034 kWh/kWp → effective 1,034 × 0.95 = **~982 kWh/kWp/yr**.

---

### Step 5 — Self-consumption (`pipeline.py → self_consumption_rate()`)
```
R = annual_yield_kwh / annual_consumption_kwh
sc_rate = HTW Berlin lookup table interpolated at R
self_consumed_kwh = annual_yield × sc_rate  (capped at demand)
exported_kwh      = annual_yield − self_consumed_kwh
```

**HTW Berlin SC table (physics-locked):**
```
R=0.0 → 100% | R=0.4 → 80% | R=1.0 → 33% | R=2.0 → 20% | R=3.0 → 15%
```

A 6 kWp system on a 4,500 kWh/yr household consumes most of its output (~80%).
A 30 kWp system on the same household exports most of it (~15% self-consumed).
This is why oversized systems have poor NPV — the scoring naturally rejects them.

---

### Step 6 — Money (`pipeline.py → simulate_economics()`)
```
Feed-in (EEG 2023): ≤10 kWp → 0.082 €/kWh | >10 kWp blended → 0.071 €/kWh
year1_savings = self_consumed_kwh × price + exported_kwh × feed_in
```

---

### Step 7 — Capex (`pipeline.py → simulate_economics()`)
```
panel_cost  = modules × cost_per_panel
bos_cost    = system_kwp × 750 €/kWp   (inverter + wiring + mounting)
service     = 2,500 €                   (planning + labor)
total_capex = panel_cost + bos_cost + service   (0% VAT since Jan 2023)
```

---

### Step 8 — Offer selection (`pipeline.py → select_options()`)
Three offers generated from all simulated candidates:

- **Budget** — lowest cost with positive NPV
- **Balanced** — best combined score of NPV + realism + self-sufficiency
- **Max Independence** — highest self-sufficiency (+ heat pump if Gas/Oil heating)

---

### Step 9 — Bill of materials (`pipeline.py → generate_bom()`)
Full component list per offer: panels, battery, inverter, wallbox, heat pump,
substructure, installation fees. Brand consistency enforced.

---

## Full wired example

```python
from app.domain.savings.solar_layer import roof_from_address
from app.domain.savings.solar_layer.pipeline import generate_offer

roof = roof_from_address("Am Nahholz 55, 74722 Buchen", floor_area_m2=150)
# → max_modules=72, orientation="SE", specific_yield=1034, source="google_solar"

result = generate_offer({
    "energy_demand_kwh": 4500,
    "energy_price_ct_kwh": 32,
    "energy_price_increase_pct": 2,
    "has_ev": False,
    "has_solar": False,
    "has_storage": False,
    "has_wallbox": False,
    "heating_existing_type": "Gas",
    "roof_type": "Concrete Tile Roof",
    "max_modules": roof.max_modules,           # ← roof cap from Google Solar
    "orientation": roof.dominant_orientation,   # ← real roof direction
    "preferred_brand": "auto",
}, overrides={
    "specific_yield": roof.specific_yield_kwh_per_kwp,  # ← real local irradiance
})

# Pipeline tries sizes from ~5 kWp to 31 kWp and picks optimal per offer type:
# Budget:           15 panels / 6.6 kWp  → €10,225, payback 11.2 yrs
# Balanced:         39 panels / 17.2 kWp → €28,585, payback 12.0 yrs
# Max Independence: 72 panels / 31.7 kWp → €70,480, payback 12.8 yrs
```

---

## Accuracy

Backtest on 1,062 real German installer projects (`merged_input_output.csv`):
- **With Google Solar roof data** → 96% of predictions within ±40% of actual install
- **Without roof data** (fixed 30 modules) → 44%

The two biggest accuracy drivers:
1. **Google Solar satellite irradiance** — beats any regional average
2. **HTW Berlin self-consumption table** — beats a flat 30% constant every time
