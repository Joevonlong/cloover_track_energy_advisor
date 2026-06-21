# Heimwende Advisor API

BFF (Backend-for-Frontend) **and** host for the pure domain core.
**All secret keys live here, in this app's env — never in the frontend.**

## Run

```bash
uv sync
uv run uvicorn app.main:app --app-dir src --reload --port 8000
```

Open http://localhost:8000/ (redirects to `/docs`).

## Test / lint

```bash
uv run pytest
uv run ruff check . && uv run mypy src
```

## Layout & owners

| Layer        | Path                | Owner            | Notes                                            |
|--------------|---------------------|------------------|--------------------------------------------------|
| `domain/`    | pure calc engine    | **Lukas (engine)** | No I/O. Savings ladder, financing, scenarios.  |
| `adapters/`  | external I/O        | **Zhou (backend)** | PVGIS, tariffs, Supabase, LLM, resolver.       |
| `api/`       | HTTP routes / deps  | **Zhou (backend)** | FastAPI routers + dependencies.                  |
| `services/`  | orchestration       | **Zhou (backend)** | Wires resolver -> engine -> llm -> persist.     |

This is a **backbone-only skeleton**: every function is a stub. Each module
docstring names its Owner and Feature ID (see `docs/feature_track/`).
