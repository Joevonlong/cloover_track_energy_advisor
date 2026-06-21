# Savings Engine — mathematical contract

Status: frozen by F03. This document is the source of truth for the pure domain core in
`apps/backend/src/app/domain/`. The OpenAPI response shape remains owned by
`specs/api/openapi.yaml`.

## 1. Invariants

- The engine is pure and deterministic: no database, network, clock, filesystem, or random input.
- Every monetary unit price is supplied in `PricingContext`; domain modules import no prices.
- Physics and policy constants may be literals only when listed in this specification.
- The canonical layer order is solar → battery → heat pump → EV charger.
- Existing equipment belongs to the starting state. Production and operation use total installed
  equipment; capex and credited savings use only the incremental delta.
- `monthly_saving = gross_saving - installment = Σ layer.delta_net` exactly.
- Rounded display values are never used as inputs to later calculations.

## 2. DD-1 decision: one credit for electrified-load PV

DD-1 is resolved in favour of the single-credit running-state model:

1. L1/L2 recompute load-aware self-consumption on total annual electricity demand:
   `base_load + heat_pump_load + ev_load`.
2. L3 prices all heat-pump electricity at the injected retail/grid price. It does not subtract a
   second `solar_covered_kwh` credit.
3. L4 prices home charging at an injected off-peak/grid blend without a second free-PV share.

This preserves the interaction between electrification and installed PV while ensuring each kWh of
PV self-consumption is credited once. The worked ladder's per-layer euro values remain illustrative;
the exact invariant is that the computed marginals sum to the headline with zero residual.

## 3. Domain inputs

### 3.1 PricingContext

All fields are required. The resolver constructs this object from `price_catalog`, location data,
and labelled financing assumptions.

| Field | Unit | Price-catalog component or source |
|---|---|---|
| `retail_price_eur_kwh` | EUR/kWh | `retail_per_kwh` plus location overlay |
| `feedin_price_eur_kwh` | EUR/kWh | `feedin_per_kwh` |
| `dynamic_spread_eur_kwh` | EUR/kWh | seeded/live dynamic-tariff source |
| `pv_per_kwp_eur` | EUR/kWp | `pv_per_kwp`, selected tier |
| `battery_per_kwh_eur` | EUR/kWh usable | `battery_per_kwh` |
| `heatpump_fixed_eur` | EUR | `heatpump_fixed` |
| `wallbox_fixed_eur` | EUR | `wallbox_fixed` |
| `oil_per_litre_eur` | EUR/litre | `oil_per_litre` |
| `gas_per_kwh_eur` | EUR/kWh | `gas_per_kwh` |
| `petrol_per_litre_eur` | EUR/litre | `petrol_per_litre` |
| `diesel_per_litre_eur` | EUR/litre | `diesel_per_litre` |
| `public_charge_per_kwh_eur` | EUR/kWh | `public_charge_per_kwh` |
| `home_charge_price_eur_kwh` | EUR/kWh | resolved off-peak/grid blend |
| `financing_apr` | fraction/year | labelled Cloover assumption |
| `financing_term_months` | months | labelled Cloover assumption |

### 3.2 Physics and policy constants

| Constant | Value |
|---|---:|
| PV-only autarky | 0.30 |
| PV+battery autarky | 0.60 |
| Battery cycles/year | 300 |
| Battery round-trip efficiency | 0.90 |
| New heat-pump SCOP, fossil replacement | 3.5 |
| New heat-pump SCOP, old-HP replacement | 4.0 |
| Default old heat-pump SCOP | 2.8 |
| Oil useful heat | 10.0 kWh/litre × 0.85 boiler efficiency |
| Gas boiler efficiency | 0.90 |
| Petrol consumption | 7.0 litres/100 km |
| Diesel consumption | 6.0 litres/100 km |
| EV consumption | 18 kWh/100 km |
| KfW default, fossil → HP | 50% |
| KfW default, old HP → new HP | 30% |
| Irradiance confidence variation | ±8% |

## 4. Intake normalisation and baseline

The canonical physical quantities are annual values.

```text
annual_consumption_kwh = electricity_eur_month × 12 / retail_price_eur_kwh

if mobility.kind == NONE:
    km_year = 0
elif km_month is supplied:
    km_year = km_month × 12
elif mobility.kind in {PETROL, DIESEL}:
    litres_year = eur_month × 12 / fuel_price_per_litre
    km_year = litres_year / consumption_l_per_100km × 100
elif mobility.kind == EV:
    kwh_year = eur_month × 12 / public_charge_per_kwh
    km_year = kwh_year / ev_consumption_kwh_per_100km × 100

current_monthly_spend =
    electricity_eur_month + heating.eur_month + mobility_baseline_eur_month
```

For direct-km input, the current mobility spend is reconstructed from `PricingContext`. For
euro-input, the supplied euro value is the baseline. `NONE` contributes zero.

Every derived/defaulted value emits an `Assumption(field, value, source, editable)`. User-provided
values use `source="user"`.

## 5. Layer formulae

### 5.1 L1 — solar

```text
added_kwp = max(0, recommended_kwp - existing_pv_kwp)
total_kwp = existing_pv_kwp + added_kwp
annual_yield_kwh = total_kwp × specific_yield_kwh_per_kwp
self_consumed_kwh = min(autarky_factor × annual_consumption_kwh, annual_yield_kwh)
exported_kwh = max(0, annual_yield_kwh - self_consumed_kwh)
gross_eur_year =
    self_consumed_kwh × retail_price_eur_kwh
    + exported_kwh × feedin_price_eur_kwh
```

When PV already exists, compare the total-state result with the existing-state result. Credit only
the difference and charge only `added_kwp`.

### 5.2 L2 — battery

```text
added_kwh = max(0, recommended_battery_kwh - existing_battery_kwh)
total_kwh = existing_battery_kwh + added_kwh
extra_self_kwh =
    min(
        (autarky_with_battery - autarky_pv_only) × annual_consumption_kwh,
        unused_pv_yield_kwh,
    )
extra_self_value =
    extra_self_kwh × (retail_price_eur_kwh - feedin_price_eur_kwh)
arbitrage_value =
    eligible_arbitrage_kwh × cycles_per_year × round_trip × dynamic_spread_eur_kwh
```

`eligible_arbitrage_kwh` excludes capacity/cycles already counted as PV shifting. Implementations
must expose the two value streams separately so overlap can be audited.

### 5.3 L3 — heat pump

Case A, fossil replacement:

```text
oil_heat_demand =
    heating_eur_month × 12 / oil_per_litre_eur × 10.0 × 0.85
gas_heat_demand =
    heating_eur_month × 12 / gas_per_kwh_eur × 0.90
hp_electricity_kwh = heat_demand_kwh / 3.5
new_heating_cost = hp_electricity_kwh × retail_price_eur_kwh
gross_eur_year = heating_eur_month × 12 - new_heating_cost
```

Case B, old heat-pump replacement:

```text
heat_demand_kwh =
    heating_eur_month × 12 / retail_price_eur_kwh × old_scop
new_hp_electricity_kwh = heat_demand_kwh / 4.0
gross_eur_year =
    (heat_demand_kwh / old_scop - new_hp_electricity_kwh)
    × retail_price_eur_kwh
```

Per DD-1, neither case applies a second PV-overlap discount. Heat-pump electricity is added to the
running state's annual electricity demand before L1/L2 are re-evaluated.

### 5.4 L4 — EV charger

```text
ev_kwh_year = km_year × 18 / 100

case A baseline =
    km_year / 100 × fuel_consumption_l_per_100km × fuel_price_per_litre
case B baseline = ev_kwh_year × public_charge_per_kwh_eur

new_cost = ev_kwh_year × home_charge_price_eur_kwh
gross_eur_year = baseline - new_cost
```

Per DD-1, `home_charge_price_eur_kwh` contains no free-PV credit. EV demand is added to the running
state before L1/L2 are re-evaluated. `NONE` and EV-with-charger produce no offer.

## 6. Financing and marginal ladder

```text
monthly_rate = annual_rate / 12
annuity(principal, annual_rate, term_months) =
    principal × monthly_rate × (1 + monthly_rate)^term_months
    / ((1 + monthly_rate)^term_months - 1)

delta_gross(layer) = gross(state_with_layer) - gross(previous_state)
delta_capex(layer) = capex_after_subsidy for incremental equipment
delta_installment(layer) = annuity(delta_capex, apr, term_months)
delta_net(layer) = delta_gross(layer) - delta_installment(layer)
monthly_saving = sum(delta_net in canonical order)
saving_after_payoff = sum(delta_gross in canonical order)
```

At zero APR, annuity is `principal / term_months`. A zero principal has a zero installment.
Subsidies are applied before financing. The default heat-pump grants are 50% for Case A and 30% for
Case B; the actual eligibility is an injected policy decision and must be labelled.

## 7. Confidence

The engine evaluates low/base/high inputs and reports the resulting monthly-saving envelope.
At minimum:

- irradiance varies by ±8%;
- dynamic-tariff spread receives the widest range;
- heat-pump subsidy spans the applicable 30–70% range;
- self-consumption/autarky is varied and named as a driver.

`biggest_driver` is the input whose low/high perturbation creates the largest absolute headline
change. The LLM may explain this output but may not calculate or alter it.

## 8. Named reference vectors

Machine-readable vectors live in
[`fixtures/savings-engine-vectors.json`](./fixtures/savings-engine-vectors.json).

- `V_WORKED_BASE`: €95 electricity + €180 oil + €160 petrol = exactly €435/month;
  base electricity ≈3,081 kWh/year; 14,800 km/year; 2,664 EV kWh/year; 9 kWp ×
  980 kWh/kWp = 8,820 kWh/year; heat-pump electricity ≈4,769 kWh/year.
- `V_BATTERY_8KWH`: €342/year extra self-use − €72/year lost feed-in + €259/year
  arbitrage = €529/year ≈€44/month gross; financing is ≈€44/month; net is within
  ±€1/month of zero.
- `V_FINANCING_180M_5PCT`: capex €13,050 / €5,600 / €11,000 / €1,200 produces monthly
  installments within €1 of €103 / €44 / €87 / €10.
- `V_WORKED_LADDER`: illustrative targets only: solar negative, battery approximately zero,
  heat pump positive, EV largest positive, final headline positive, and after-payoff saving much
  larger. A ±15% magnitude tolerance applies to the documented targets.
- `V_OWNED_EQUIPMENT`: installed PV/battery are carried into the starting state; capex and yield
  credit apply only to the positive delta.

The ladder fixture stores unrounded net targets whose sum is the target headline. An implementation's
own exact values replace these illustrative figures in F24; its computed `Σ delta_net` must equal its
headline exactly, without tolerance.

## 9. Mapping to the API contract

For each cumulative rung:

- gross bucket values map to `ScenarioResult.breakdown`;
- cumulative capex maps to `ScenarioResult.capex`;
- cumulative installment maps to `installment_eur_month`;
- exact `Σ delta_net` maps to `monthly_saving_eur`;
- exact `Σ delta_gross` maps to `saving_after_payoff_eur`;
- confidence evaluation maps to `ScenarioResult.confidence`.

No F03 field extends or changes the frozen OpenAPI schema.
