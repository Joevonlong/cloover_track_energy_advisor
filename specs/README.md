# `specs/` — the frozen contract (source of truth)

These artifacts are the **seam** the whole team builds against. They **win over** prose docs
(`docs/design_plan/system_workflow.md`) when they disagree.

| File | What | Authored by | Status |
|------|------|-------------|--------|
| `api/openapi.yaml` | The HTTP contract — request/response schemas. FE generates its TS client from it; BE generates Pydantic models. | **F02** (Zhou, rev Lukas) | 🟡 **placeholder skeleton** — freeze in F02 |
| `domain/savings-engine.spec.md` | The math — every formula + the §8 worked example as test vectors the engine is TDD'd against. | **F03** (Lukas, rev Zhou) | 🟡 **placeholder** — author in F03 |

> Do not build features against the placeholders. **F02 and F03 are the first things to do (P0).**
> Until then they only mark *where* the contract lives. See `docs/feature_track/specs/F02-*`, `F03-*`.
