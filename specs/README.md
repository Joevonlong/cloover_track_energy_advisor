# `specs/` — the frozen contract (source of truth)

These artifacts are the **seam** the whole team builds against. They **win over** prose docs
(`docs/design_plan/system_workflow.md`) when they disagree.

| File | What | Authored by | Status |
|------|------|-------------|--------|
| `api/openapi.yaml` | The HTTP contract — request/response schemas. FE generates its TS client from it; BE generates Pydantic models. | **F02** (Zhou, rev Lukas) | ✅ frozen; optional HP fields added with F05 |
| `domain/savings-engine.spec.md` | The math — every formula + the §8 worked example as test vectors the engine is TDD'd against. | **F03** (Lukas, rev Zhou) | ✅ frozen with machine-checkable vectors |

> Build downstream features against these files. Contract changes must update the generated/manual
> backend and frontend types in the same feature.
