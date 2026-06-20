# Workflow

## Questions for later:

- Output Data during meeting ?
- Output Data before meeting ?
- Extract Audio -> Fill out input or input manually

## Input from customer:

- House adress -> Street, City, Postcode
- Add mobilty spending if petrol/diesl/ev -> km or cost per month
  - Monthly electricity bill
  - Monthly gas/ oil bill
- Floor area, building year, people

## Layer 1 : Permit

| Product | Check | Source | Result |
|---------|-------|--------|--------|
| Solar PV | Zone type + solar permitted | Bebauungsplan RAG | 🟢 Permitted (cited clause) / 🔴 Restricted |
| Solar PV | Heritage protection | BayernAtlas Denkmalschutz API | 🟢 Not listed / 🔴 Listed — blocked |
| Solar PV | Neighbourhood precedent | MaStR by PLZ | 🟢 40+ systems / 🟡 5-40 / 🔴 0-5 |
| Heat pump | Outdoor unit permitted + noise zone | Bebauungsplan RAG | 🟢 Permitted / 🟡 Noise check needed / 🔴 Restricted |
| Heat pump | Heritage protection | BayernAtlas Denkmalschutz API | 🟢 Not listed / 🟡 Listed — approval needed |
| Heat pump | Boiler age — GEG 2024 | Hardcoded rule | 🟢 Replacement permitted / 🔴 Protected until 2029 |
| EV Charger | Private parking available | OSM tag + user checkbox | 🟢 Private driveway/garage / 🔴 Street only — blocked |
| EV Charger | Apartment building — WEG | OSM building type | 🟢 Single family / 🟡 Apartment — owner vote needed |
| Battery | Indoor installation | Hardcoded rule | 🟢 Always permitted — no approval needed |
| Battery | Grid registration | Hardcoded advisory | ℹ️ Must register in MaStR after install — installer task |

Three data sources cover everything:

- Bebauungsplan RAG → Solar + Heat pump
- BayernAtlas API → Solar + Heat pump
- MaStR API → Solar
- OSM Overpass → EV charger (already in your stack)
- Two hardcoded rules → Heat pump GEG + Battery

## Layer 2: Google Solar + Solar Check AND Battery Option

- How big a system fits on this roof (kWp)
- How much electricity it produces per year (kWh)
- How much of that electricity the household actually uses themselves vs feeds into the grid (self-consumption ratio)

- steal tectum solar-pipline to calculate this!

---

- Google Solar API takes the address coordinates and returns the roof data — segments, area, pitch, azimuth, shading — already computed from satellite
- Best roof segments selected (south-facing, low shading)
- Panel count calculated from usable roof area (1 panel = 1.7m², 380Wp each)
- System kWp = panel count × 0.38
- Annual yield kWh = system kWp × sunshine hours × performance ratio
- Self-consumption split: 30% used by household without battery, 70% with battery
- Monthly electricity saving = yield × self-consumption × grid price
- Monthly feed-in revenue = remaining yield × €0.082 EEG rate
- Monthly battery arbitrage = remaining grid electricity × 34% dynamic tariff saving
- Output: total electricity bucket in €/month → feeds the savings engine

### Output of the solar layer

Three numbers that feed the savings engine:

```
system_kwp          → e.g. 9.5 kWp
annual_yield_kwh    → e.g. 9,230 kWh/year  (from Google Solar API irradiance)
self_consumption_pct → 30% without battery / 70% with battery

monthly_electricity_saving = annual_yield × self_consumption × grid_price ÷ 12
monthly_feedin_revenue     = annual_yield × (1 - self_consumption) × 0.082 ÷ 12
monthly_battery_arbitrage  = remaining_grid_kwh × 34% saving on dynamic tariff ÷ 12

TOTAL electricity bucket = saving + feed-in + arbitrage = €X/month
```

## Layer 3: HeatPump

The full heat pump calculation with these three inputs:

```
1. building_year → heat_load_factor (hardcoded table)

2. heat_load_factor × floor_area ÷ 1000 = required_kW
   → round up to: 6/8/10/12/14/16 kW

3. annual_heat_demand = required_kW × 1800 hours

4. annual_electricity = annual_heat_demand ÷ 3.5 (COP)

5. solar_covers = annual_electricity × overlap_factor
   (0.2 without battery, 0.4 with battery)

6. net_electricity_cost = (annual_electricity - solar_covers)
                          × grid_price ÷ 12

7. monthly_saving = current_heating_cost - net_electricity_cost
```

## Layer 4: EV

input need: how many km mobile spend each year, (petrol or ev)

```
km_year = mobility_spend / fuel_price × consumption_l_per_100km   # back out distance
ev_kwh  = km_year × ev_consumption(kWh/100km) / 100
ev_charging_cost = ev_kwh × charging_price (off-peak dynamic / PV surplus blend)
mobility_savings = mobility_spend − ev_charging_cost
```

- Charging price is a **blend**: PV surplus (≈ free), off-peak dynamic tariff, occasional public
- charging. The off-peak + PV blend is where the saving comes from — again ties back to the tariff.

## Layer 5:

```
BASELINE = electricity bill + heating cost + fuel cost
         = €120 + €180 + €150 = €450/month

ELECTRICITY BUCKET = solar saving + feed-in + battery arbitrage
HEATING BUCKET     = current heating cost - heat pump running cost
MOBILITY BUCKET    = current fuel cost - EV charging cost

FOUR SCENARIOS ranked by North Star:
Solar only       = electricity bucket - installment
PV + battery     = electricity + arbitrage - installment
+ heat pump ★    = electricity + heating - installment
+ EV charger     = electricity + heating + mobility - installment
```

### Dashboard:

- **YOUR SAVING: €187/month** — biggest text on the page, top center
- Before vs after: "Today you pay €450/month → After Cloover bundle €263/month"
- How long until it pays off: "Bundle pays for itself by 2031"
- What's included in the bundle — simple icons: ☀️ Solar 9.5kWp · 🔋 Battery · ♨️ Heat pump · 🚗 EV charger
- What you get for free: smart meter, dynamic tariff, Cloover energy manager
- Your roof: south-facing, 62m² usable, 47 neighbours already did it
- Permits: all green ✓
- Your investment: €34,000 gross → €22,000 after grants → €143/month financing
- Cash-flow positive from day one
- Claude paragraph in plain German — 3 sentences why this works for your home specifically
- One big green button at the bottom: **Apply for Cloover financing**
