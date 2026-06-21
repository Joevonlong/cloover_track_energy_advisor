# Heimwende — Web (Vite SPA)

Frontend for the Heimwende Energy Advisor. **Vite + React + TS + Tailwind**, owned by **Philips**.
The SPA only calls the FastAPI backend; the **only** env var is `VITE_API_BASE_URL` (no secrets in the bundle).

## Run

```bash
cp .env.example .env          # VITE_API_BASE_URL=http://localhost:8000
pnpm install
pnpm dev                      # http://localhost:5173
```

The backend must be running on :8000 (see `../api`). `pnpm build` type-checks + builds; `pnpm typecheck` / `pnpm lint`.

## Structure (backbone — fill in the TODOs)

- `src/App.tsx` — app shell (hero placeholder + API health badge)
- `src/lib/api.ts` — fetch client → **replace with the F02-generated OpenAPI client**
- `src/lib/types.ts` — placeholder types → replace with generated client types (F02)
- `src/features/intake/` — **F19** · `configurator/` — **F20** · `dashboard/` — **F21/F22** · `proposal/` — **F23**
- `src/components/` — shared UI (later)
