# Heimwende Energy Advisor

> **Berlin Energy AI Hackathon 2026** · Cloover Challenge

An AI-powered home energy transition advisor that calculates one clear number: **how much a household saves per month** after a full home-energy upgrade (solar, battery, heat pump, EV charger) combined with financing and a dynamic tariff — presented as a single product.

---

## The Problem

Today, customers are sold an energy installation first and a tariff bolted on afterwards. That's backwards.

This tool builds a single checkout / advisor that sells the *outcome*: a complete home-energy upgrade with financing and a dynamic tariff, front-and-centre as one monthly saving number.

## North Star Metric

**Monthly saving** = what the household pays today − (upgrade installment + new energy costs)

Where the installment outweighs early savings, we show it honestly — e.g. *"near cost-neutral now, €X/month saved once it's paid off."*

## Upgrade Scenarios Modelled

| Configuration | Savings Buckets |
|---|---|
| Solar only | Electricity (self-consumption) |
| PV + Battery | Electricity + dynamic tariff arbitrage |
| PV + Battery + Heat Pump | + Heating (replaces oil/gas) |
| PV + Battery + Heat Pump + EV Charger | + Mobility (replaces petrol) |

The advisor picks the configuration that delivers the **largest monthly saving** per household profile.

## How It Works

1. **Minimal input** — household size, current electricity/heating/mobility spend, postcode
2. **AI modelling** — LLM advisor models savings across all scenarios using local irradiance, grid fees, applicable subsidies, and self-consumption ratios
3. **Clear output** — ranked upgrade paths with plain-language explanation; copy an installer could paste straight into a customer proposal
4. **Up-sell framing** — spots the obvious next step and quantifies it (e.g. *"still on oil heating? A heat pump saves you €X/month"*)

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | **Vite + React + TypeScript + Tailwind** SPA · TanStack Query · React Hook Form + Zod |
| Backend | **FastAPI** (Python 3.12, **uv**) — the only server; hosts the BFF **and** the pure domain core |
| Data | **Supabase** (Postgres) — reference data, `price_catalog`, runs, proposals |
| LLM | Provider-agnostic adapter, **Claude** default (explains/sells — **never computes** the number) |
| Contract | `specs/api/openapi.yaml` → generated TS client (FE) + Pydantic models (BE) |

> **No secret in the frontend bundle** — the only FE env var is `VITE_API_BASE_URL`; all keys live in FastAPI's env.

## Repository structure

```
apps/
  api/   FastAPI BFF + pure domain core              ← backend (Zhou) · domain/ (Lukas)
    src/app/domain/    pure engine: layers 1–4, optimiser, financing   (Lukas)
    src/app/adapters/  PVGIS · tariff · resolver · site-check · llm     (Zhou)
    src/app/api/       routes (/recommend, /site-check) · deps          (Zhou)
    src/app/services/  recommendation orchestration                     (Zhou)
  web/   Vite + React + TS + Tailwind SPA             ← frontend (Philips)
    src/features/      intake · configurator · dashboard · proposal
specs/   frozen contract (openapi.yaml = F02) + domain math spec (F03)
docs/    design_plan/system_workflow.md (blueprint) · feature_track/ (specs, backlog, timeline)
```

> **Who builds what & when:** see [`docs/feature_track/`](docs/feature_track/) — the feature backlog,
> the spec-based process, and the build timeline. Each module below is stubbed and tagged with its
> owner + feature ID (e.g. `TODO F06 (Lukas)`).

## Getting Started

This is a monorepo with two apps. Run the backend and frontend in two terminals.

```bash
git clone git@github.com:Joevonlong/heimwende-energy-advisor.git
cd heimwende-energy-advisor

# 1) Backend — FastAPI on http://localhost:8000
cd apps/backend
cp .env.example .env            # fill keys later; the skeleton boots without them
uv sync
uv run uvicorn app.main:app --app-dir src --reload --port 8000
#   check: curl http://localhost:8000/health  →  {"status":"ok",...}

# 2) Frontend — Vite on http://localhost:5173  (new terminal)
cd apps/frontend
cp .env.example .env            # VITE_API_BASE_URL=http://localhost:8000
pnpm install
pnpm dev
```

Or use the root `Makefile`: `make install`, then `make api-dev` / `make web-dev`.

> **Status:** F01–F05 foundations are implemented: monorepo, frozen API/domain contracts,
> offline price catalog, and pure intake normalisation. F06–F27 continue the savings layers,
> adapters, recommendation orchestration, and product UI.

## Team

Built at the **Berlin Energy AI Hackathon — June 20, 2026** for the [Cloover](https://cloover.com) challenge track.

Prize: AirPods + Powerbank per team member 🏆
