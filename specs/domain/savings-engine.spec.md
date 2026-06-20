# Savings Engine — domain math spec (PLACEHOLDER)

> 🟡 **Placeholder — authored in feature F03** (`docs/feature_track/specs/F03-domain-spec.spec.md`).
> This file will formalise every formula and pin the §8 worked example as named test vectors the
> pure engine (F05–F11) is TDD'd against. Until then, the math lives in
> [`docs/design_plan/system_workflow.md`](../../docs/design_plan/system_workflow.md) §5–§8.

The North Star: `monthly_saving = current_spend − (loan_installment + new_energy_cost)`.

Four stacked layers (pure, zero-I/O, deterministic):

1. **L1 Solar** (`domain/savings/electricity.py`) — §5.1 — *Lukas / F06*
2. **L2 Battery** (`domain/savings/electricity.py`) — §5.2 / §8.1 — *Lukas / F07*
3. **L3 Heat pump** (`domain/savings/heating.py`) — §5.3 — *Lukas / F08*
4. **L4 EV charger** (`domain/savings/mobility.py`) — §5.4 — *Lukas / F09*

Plus: optimiser + marginals (`options.py`/`scenarios.py`, §6, *F10*), financing + confidence
(`financing.py`, §6.5/§7, *F11*).

> ⚠️ **Resolve DD-1 first** (single-credit accounting for PV self-consumption of HP/EV load — see
> F03 §0) before coding L3/L4, or the per-bucket numbers will double-count. Prices are **injected**
> via `PricingContext` (from `price_catalog`), never imported (§12).
