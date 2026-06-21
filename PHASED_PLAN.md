# Plan: Attachable 3D House Modules

Toy/gimmick layer: four toggleable, animated energy props (☀️ solar panel,
♨️ heat pump, 🔋 battery, 🚗 EV charger) on the live `viewing` 3D stage.
Spec: `apps/frontend/data/3d_modules.md`. No new deps, no contract change, no
money math. Toggles are always interactive; the recommendation auto-seeds them
once when it first lands.

## Progress
- [ ] Phase 1: Foundation — footprint exposure, anchor math, toggle bar
- [ ] Phase 2: The four real modules + animations
- [ ] Phase 3: Auto-seed from recommendation + polish

---

## Phase 1: Foundation — footprint exposure, anchor math, toggle bar
**Goal:** Expose footprint axes from the geometry engine, add a `moduleSlots()`
placement helper, and render an always-interactive toggle bar that pops one
placeholder box onto the house.
**Effort:** ~2–3 hours

Steps:
1. `roofGeometry.ts`: add `footprint: { u, v, halfLong, halfShort }` to
   `HouseGeometry` and return it from all four builders.
2. Add `ModuleKind` ("pv" | "battery" | "heat_pump" | "ev") and `ModuleSlot`
   (kind, position, rotationY, optional surface).
3. Add `moduleSlots(geo, params)` computing each anchor from the spec (heat pump
   ground spot, battery +u wall, EV −v wall, PV = surface whose azimuth is
   closest to south/180°).
4. New `houseModules.tsx`: `<HouseModule kind slot>` rendering a placeholder box
   with a drop/scale-in mount animation via `useFrame`.
5. `HouseCanvas.tsx`: add `addons: Record<ModuleKind, boolean>` prop; memo slots;
   render enabled modules inside the `<House>` group.
6. `IntakeScreen.tsx`: `addons` state (all off) + floating chip toggle bar over
   the stage; style in `index.css`.
7. `pnpm typecheck` + `pnpm lint`; preview toggling across all roof types.

**Risk:** PV sun-facing surface selection on flat/hip relies on `surfaces[]`
azimuth; placeholder phase de-risks anchoring before real meshes.

---

## Phase 2: The four real modules + animations
**Goal:** Replace placeholders with the real props and their looping animations.
**Effort:** ~3–4 hours

Steps:
1. ☀️ Solar panel — single 1.7×1.0×0.04 m slab + frame + cell lines in the
   surface plane (oriented via normal, +0.05 offset), glassy blue, emissive
   glint sweep.
2. ♨️ Heat pump — condenser box + recessed fan disc with blades + pipe stub;
   fan spins, housing breathes ±2%, hub glows on a sine.
3. 🔋 Battery — rounded slab + inset charge bar + edge LED; bar fills 0→100% then
   holds, LED breathes.
4. 🚗 EV charger — wallbox + emissive LED ring + curled cable; ring breathing +
   travelling dot.
5. Materials per spec, memoized.
6. `pnpm typecheck` + `pnpm lint`; preview each on gable/hip/shed/flat.

**Risk:** Must memoize materials/geometries so toggling doesn't re-allocate.

---

## Phase 3: Auto-seed from recommendation + polish
**Goal:** Seed toggles once from the best scenario when the recommendation lands,
plus final visual polish.
**Effort:** ~1–2 hours

Steps:
1. `IntakeScreen.tsx`: track `userTouchedAddons`; when `recStatus` first flips to
   `ready`, map `best`'s index in `alternatives[]` to the cumulative rung set and
   seed `addons` — only if the user hasn't touched the toggles.
2. Map `best.scenario_id` to its position in `alternatives[]` for the rung.
3. Toggle-bar polish: active styling, emoji + label, entrance; ensure it doesn't
   fight `OrbitControls` pointer events.
4. Final `pnpm typecheck` + `pnpm lint` + full preview pass.

**Risk:** If `best.scenario_id` doesn't index `alternatives[]`, fall back to
matching by `monthly_saving_eur`.
