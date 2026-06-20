---
id: F26
title: Subsidy catalog (DB-driven, official-sourced, cited)
epic: E2 Backend & Adapters
owner: Zhou
reviewers: [Lukas]
co_owners: [Lukas]
priority: P2
mvp: true
status: Ready
branch: feat/F26-subsidy-catalog
depends_on: [F04]
contract_impact: reads
estimate_h: 1.5
---

# F26 — Subsidy catalog (DB-driven, official-sourced, cited)

> **North-Star link:** Every subsidy reduces `capex_after_subsidy` and therefore the `installment` term
> in `monthly_saving = gross_saving − installment`. Keeping subsidies in a cited, DB-driven table means
> the KfW 458 grant and 0 % VAT are always correct, auditable, and the demo never over-claims them.

## 1. Intent (what & why)

Implement R-C (§0, §12.1): subsidies must never be hard-coded in application code — they live in a
Supabase **`subsidy_catalog`** table (analogous to `price_catalog`, §12) where each row carries an
**official/legal `source_url` + `valid_from`/`valid_until`** date, a rate or cap, and a notes field.
The Resolver (F12) reads qualifying rows and builds a **`SubsidyContext`** which is injected into the
financing engine (F11), mirroring the `price_catalog` → `PricingContext` pattern. Each applied subsidy
is cited back to the user via an `assumptions[]` / `subsidy_note` in the response (§6.5, §6.6, §14.1).
Lukas verifies the official sources; Zhou builds the table, seed migration, and resolver adapter.

## 2. Scope

**In scope**
- Supabase table `subsidy_catalog` with the §12.1 schema (programme, component, rate, cap_eur, unit, source_url, valid_from, valid_until, notes).
- Seed with the six MVP rows from §12.1: `kfw_458_base` (heat_pump_a + heat_pump_b), `kfw_458_speed_bonus` (heat_pump_a only), `vat_pv_battery` (pv + battery), `bafa_ev_umweltbonus` (ev_charger, rate 0 / cap 0).
- Resolver adapter that queries `WHERE valid_from ≤ today AND (valid_until IS NULL OR valid_until ≥ today)` and builds `SubsidyContext` for injection into F11.
- Each applied subsidy emits an `Assumption { label, rate, cap_eur, source_url }` entry in the response.
- Manual pre-demo re-verification procedure: Lukas checks each row against its `source_url` before the demo and signs off; documented in the seed file header comment.
- Documented stretch: a GitHub Actions scheduled workflow that runs a weekly HEAD-check against each `source_url` and opens a PR on 404 / redirect — see §12.1.

**Out of scope** (explicitly, to prevent creep)
- The financing engine itself (annuity, break-even) → **F11**.
- Reading or building `PricingContext` → **F12**.
- Auto-parsing rate changes from KfW Merkblatt → stretch beyond the HEAD-check.
- Länder/municipal subsidy rows (e.g. Bayern, BW) → optional stretch seed, not MVP.
- Any UI rendering of subsidy chips → **F22/F23** (they consume `assumptions[]`).

## 3. Functional requirements

| # | Requirement | Source (§) |
|---|-------------|-----------|
| R1 | `subsidy_catalog` table exists with the exact §12.1 column set and `PRIMARY KEY (programme, component, valid_from)`. | §12.1, §14.3 |
| R2 | Seed contains all six MVP rows (§12.1 seed table) with non-null `source_url` on every row. | §12.1 |
| R3 | `bafa_ev_umweltbonus` row has `rate = 0` and `cap_eur = 0`, notes "ended 17 Dec 2023", reflecting the ended Umweltbonus (§6.5). | §6.5, §12.1 |
| R4 | `kfw_458_speed_bonus` applies only to `heat_pump_a` (fossil→HP); `heat_pump_b` (old-HP→HP) has no speed-bonus row — consistent with the KfW Case-B nuance (§5.3, §6.5). | §5.3, §6.5, §12.1 |
| R5 | Resolver queries rows with `valid_from ≤ request_date AND (valid_until IS NULL OR valid_until ≥ request_date)` and builds `SubsidyContext` — expired rows are automatically excluded without code changes. | §12.1 |
| R6 | Engine (F11) reads `SubsidyContext` and never imports subsidy constants directly — verified by code grep. | §12.1, §12 (mirror pattern) |
| R7 | For each applied subsidy, the response includes an `Assumption { label, rate, cap_eur, source_url }` entry in `assumptions[]`. | §6.5, §6.6, §14.1 |
| R8 | Combined KfW 458 grant for Case A (base 0.30 + speed 0.20 = 0.50) matches the §6.5 default of 50 %; capped at 70 % of eligible cost and €21,000 (the engine enforces the cap). | §6.5 |
| R9 | Seed is idempotent and offline-safe (no network required to run). | §13.2, §15 |

## 4. Data, formulas & sources

> All rates come from the official pages cited in §6.5, §11, §12.1. No number is invented.

| Quantity / call | Value | Official source | Fallback | Used in |
|---|---|---|---|---|
| KfW 458 base rate | 0.30 (fraction_of_capex) | [KfW 458](https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/Förderprodukte/Heizungsförderung-für-Privatpersonen-Wohngebäude-(458)/) | constants §10 | §6.5 financing · L3 capex |
| KfW 458 Klima-Geschwindigkeitsbonus | 0.20 (heat_pump_a only) | [KfW 458](https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/Förderprodukte/Heizungsförderung-für-Privatpersonen-Wohngebäude-(458)/) | 0.00 if not applicable | §6.5 · Case A only |
| KfW 458 cap | €21,000 (max 70 % of eligible) | KfW 458 Merkblatt | — | F11 cap enforcement |
| 0 % VAT — PV + battery | 0.00 (fraction_of_capex) | [§12(3) UStG](https://www.gesetze-im-internet.de/ustg_1980/__12.html) | — | §6.5 · L1/L2 capex |
| BAFA EV Umweltbonus | 0.00 (ended 17 Dec 2023) | [BAFA](https://www.bafa.de/DE/Energie/Energieeffizienz/Elektromobilitaet/elektromobilitaet_node.html) | — | §6.5 · L4 capex |

Engine flow (from §12.1):
```
Resolver queries subsidy_catalog
  WHERE component = <layer>
  AND   valid_from  ≤ today
  AND   (valid_until IS NULL OR valid_until ≥ today)
→ builds SubsidyContext
→ injected alongside PricingContext into F11

F11 financing step:
  total_rate = min(sum(matching row rates), 0.70)   # KfW hard cap
  grant      = min(total_rate × capex, cap_eur)
  capex_after_subsidy = capex − grant
  # emits Assumption { label, rate, cap_eur, source_url } per row
```

## 5. Contract surface

`contract_impact: reads` — F26 adds no new response fields to `openapi.yaml`; the `assumptions[]`
array already exists in the contract (F02). The `SubsidyContext` is an internal server-side struct
(mirroring `PricingContext`) that the engine consumes; it does not appear on the wire.

- The `source_url` field from applied subsidy rows is propagated into each `Assumption` object's
  existing `source` field in the response.
- No backwards-incompatible schema change; existing consumers of `assumptions[]` see additional
  entries with no structural change.

## 6. Acceptance criteria (testable — these become the tests)

- [ ] **AC1** — Given a fresh DB, when the F26 migration runs, then `subsidy_catalog` exists with columns `(programme, component, rate, cap_eur, unit, source_url, valid_from, valid_until, notes)` and PK `(programme, component, valid_from)`.
- [ ] **AC2** — Given the seed, when `subsidy_catalog` is queried, then exactly six MVP rows are present, each with a non-null `source_url`.
- [ ] **AC3** — Given `component = 'heat_pump_a'` and today's date, when the resolver queries eligible rows, then it returns both `kfw_458_base` (rate 0.30) and `kfw_458_speed_bonus` (rate 0.20); their sum (0.50) matches the §6.5 fossil→HP default.
- [ ] **AC4** — Given `component = 'heat_pump_b'`, when the resolver queries, then only `kfw_458_base` (rate 0.30) is returned — no speed-bonus row — matching the Case-B nuance of §5.3.
- [ ] **AC5** — Given a row with `valid_until = '2023-12-17'` (bafa_ev row), when the resolver queries for today > 2023-12-17, then the row is excluded from `SubsidyContext` (engine receives zero subsidy for ev_charger).
- [ ] **AC6** — Given the engine (F11) receives `SubsidyContext`, when it computes `capex_after_subsidy`, then the source code contains zero hard-coded subsidy constants (verified by grep for `0.30`, `0.50`, `0.20` in domain modules).
- [ ] **AC7** — Given a Case-A fossil→HP with `capex = €22,000`, when the engine applies the two KfW rows, then `capex_after_subsidy = max(22000 − 0.50 × 22000, 22000 − 21000) = €11,000`, and the response `assumptions[]` contains two entries each with a non-null `source_url` pointing to the KfW 458 page.

## 7. Test plan

- **Unit** (pure, zero I/O): mock `SubsidyContext` with the §12.1 seed values; assert F11 cap logic (AC7 worked example); assert zero-grant path for `bafa_ev_umweltbonus`; assert Case-B returns only base rate.
- **Integration / contract**: a resolver test that queries a real (test) Supabase instance seeded by the F26 migration; asserts the returned `SubsidyContext` matches the six seed rows; asserts `assumptions[]` in the F17 response includes `source_url`.
- **Demo-safety**: run the seed and a SubsidyContext query with networking disabled — must succeed (AC5 / §13.2).

## 8. Dependencies & interfaces

- **Upstream (needs):** **F04** (Supabase instance exists; migration pattern established; `price_catalog` is the analogous table to mirror).
- **Downstream (feeds):** **F11** (financing engine — consumes `SubsidyContext`); **F12** (resolver builds `SubsidyContext` from this table); **F22/F23** (UI renders `assumptions[]` subsidy citations).
- **Mock until ready:** F11 and F12 mock `SubsidyContext` as an in-memory struct using the §12.1 seed values (same numbers as the seed), then swap to the DB read once F26 lands — identical to how F04 is mocked.

## 9. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| KfW Merkblatt changes rate/cap before demo | `valid_until` gates expired rows out automatically (§12.1, §15); Lukas re-verifies each `source_url` before demo (documented in seed header). |
| Speed-bonus applied to Case B (over-claiming) | R4 + AC4 explicitly test that `heat_pump_b` returns no speed-bonus row; a notes field explains why (§5.3). |
| Engine imports a subsidy constant directly | AC6 grep catches this; the mirror pattern from F04/F12 (`price_catalog` → `PricingContext`) is the enforced design. |
| Source URL goes 404 before demo | Stretch HEAD-check GH Actions (§12.1); fallback: Lukas re-verifies manually and updates the URL in one DB row, no redeploy. |
| Länder rows added without verification | Länder rows are stretch (not seeded MVP); any addition requires Lukas sign-off on the `source_url` before merge. |

## 10. Definition of Done (checklist)

- [ ] All acceptance criteria pass as automated tests (migration + seed + resolver query + F11 cap assertion + grep).
- [ ] Lint + type-check clean (`ruff`+`mypy`).
- [ ] Contract honored — `contract_impact: reads`; no structural change to `openapi.yaml`; `assumptions[]` entries carry `source_url`.
- [ ] No hard-coded subsidy constant in engine/adapter code (AC6 grep passes).
- [ ] Every seed row has a non-null `source_url`; Lukas has verified each URL against the official page and signed off.
- [ ] `valid_until` gating is exercised by AC5 test.
- [ ] Reviewed by Lukas (source verification + engine pattern review); merged to `main`; main is green.
- [ ] Demo happy-path runs offline after merge (seed query needs no network).

## 11. References

- `docs/design_plan/system_workflow.md` §12.1 (subsidy_catalog schema + seed), §6.5 (KfW/VAT/BAFA financing), §5.3 (Case B KfW nuance), §6.6 (cited subsidy in strategies), §14.1 (assumptions[] in contract), §14.3 (Supabase schema), §12 (price_catalog mirror pattern), §13.2 (offline demo), §15 (risks).
- `docs/feature_track/FEATURE_BACKLOG.md` §2.1 R-C row, §2 D10, §3 E2 row F26.
- `specs/domain/savings-engine.spec.md` §6 (financing step; `SubsidyContext` injected before annuity).
- `specs/api/openapi.yaml` — `assumptions[]` array (no structural change required).
