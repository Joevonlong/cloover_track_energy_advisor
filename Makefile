# Heimwende Energy Advisor — dev shortcuts
# Backbone (F01). Backend = apps/api (FastAPI/uv) · Frontend = apps/web (Vite).
#
# ── Contract codegen (F02 — FROZEN) ────────────────────────────────────────
# The hand-authored files are the committed source of truth until tooling is
# installed.  Once `uv` + `pnpm` are available these targets regenerate both
# layers from the single frozen openapi.yaml:
#
#   gen-models  →  re-generates apps/api/src/app/domain/models.py from the YAML
#   gen-client  →  re-generates apps/web/src/lib/api-types.ts from the YAML
#
# Run both in the same commit whenever openapi.yaml changes (Backlog §6).
# ───────────────────────────────────────────────────────────────────────────

.PHONY: help install api-install web-install api-dev web-dev api-test api-lint web-build dev gen-models gen-client

help:
	@echo "Heimwende — make targets:"
	@echo "  make install      install backend (uv) + frontend (pnpm) deps"
	@echo "  make api-dev      run FastAPI on http://localhost:8000"
	@echo "  make web-dev      run Vite SPA on http://localhost:5173"
	@echo "  make api-test     run backend tests (pytest)"
	@echo "  make api-lint     ruff + mypy"
	@echo "  make web-build    type-check + build the SPA"
	@echo "  make dev          how to run both (two terminals)"
	@echo "  make gen-models   regenerate Pydantic models from openapi.yaml (needs uv + datamodel-codegen)"
	@echo "  make gen-client   regenerate TS types from openapi.yaml (needs pnpm + openapi-typescript)"

install: api-install web-install

api-install:
	cd apps/api && uv sync

web-install:
	cd apps/web && pnpm install

api-dev:
	cd apps/api && uv run uvicorn app.main:app --app-dir src --reload --port 8000

web-dev:
	cd apps/web && pnpm dev

api-test:
	cd apps/api && uv run pytest

api-lint:
	cd apps/api && uv run ruff check . && uv run mypy src

web-build:
	cd apps/web && pnpm build

dev:
	@echo "Run in two terminals:  make api-dev   |   make web-dev"

# ── Contract codegen (F02) — run these once tooling is installed ────────────

# Regenerate Pydantic v2 models from the frozen openapi.yaml.
# Requires: uv + datamodel-codegen (pip install datamodel-code-generator).
# The hand-authored models.py is the committed source until this runs.
gen-models:
	datamodel-codegen \
	  --input specs/api/openapi.yaml \
	  --input-file-type openapi \
	  --output apps/api/src/app/domain/models.py \
	  --target-python-version 3.12 \
	  --use-annotated \
	  --use-field-description

# Regenerate TypeScript types from the frozen openapi.yaml.
# Requires: pnpm + openapi-typescript (pnpm add -D openapi-typescript).
# The hand-authored types.ts is the committed source until this runs.
# Output goes to api-types.ts (the generated file); types.ts stays as the
# hand-maintained alias / extension point.
gen-client:
	pnpm --dir apps/web dlx openapi-typescript \
	  ../../specs/api/openapi.yaml \
	  -o src/lib/api-types.ts
