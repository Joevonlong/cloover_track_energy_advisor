# Plan: Phase 4 — 3D Model Generation ("The Wow Moment")

## Progress
- [ ] Phase 4A: Geometry Engine
- [ ] Phase 4B: R3F Canvas + Pactum Split-View Layout
- [ ] Phase 4C: POST /recommend Wiring

---

## Phase 4A: Geometry Engine
**Goal:** Pure TypeScript module converting `(LatLng[] | null) + RoofParams` → Three.js geometry + `RoofPlacementSurface[]`
**Effort:** ~2h

Steps:
1. `pnpm add @react-three/fiber @react-three/drei` in `apps/frontend/`
2. Create `src/features/viewer/roofGeometry.ts`:
   - Define `RoofPlacementSurface` type (per `3d_building.md` spec)
   - `latLngToLocal(polygon: LatLng[]): { x: number; z: number }[]` — Turf.js rhumbBearing + rhumbDistance to convert lat/lng corners to local metre-space
   - `DEFAULT_FOOTPRINT` constant: 10m × 8m rectangle (used when polygon is null)
   - `buildFlatRoof(footprint, wallHeightM)` → `{ geometries: BufferGeometry[]; surfaces: RoofPlacementSurface[] }`
   - `buildGableRoof(footprint, wallHeightM, pitchDeg)` → same; ridge = `Math.tan(pitchRad) * (widthM / 2)`
   - `buildHouseGeometry(polygon: LatLng[] | null, params: RoofParams)` — dispatches to flat/gable; hip/shed fall back to gable for MVP
3. Fix hidden dep: add `useState<Household | null>` to `IntakeScreen` and wire `IntakeForm`'s `onComplete` to store it

**Risk:** Turf.js bearing computation must preserve real-world azimuth so panels face the correct direction later. Use `rhumbBearing` + `rhumbDistance`, not great-circle distance.

---

## Phase 4B: R3F Canvas + Pactum Split-View Layout
**Goal:** Pactum-style full layout with animated 3D house on the left and activity feed on the right
**Effort:** ~2h

Steps:
1. Create `src/features/viewer/HouseCanvas.tsx`:
   - `<Canvas>` with perspective camera (`fov 45`, positioned at `[0, 8, 14]`)
   - `<ambientLight intensity={0.5}>` + `<directionalLight position={[5,10,5]} castShadow>`
   - Ground plane mesh (subtle grey, 30m × 30m)
   - House mesh group from `buildHouseGeometry` result; light grey `MeshStandardMaterial`
   - Extrude-up animation: `useFrame` lerps `mesh.scale.y` 0→1 over ~1s
   - `<OrbitControls enableDamping dampingFactor={0.05} />` from drei
2. Create `src/features/activity/ActivityFeed.tsx`:
   - Right panel styled to match Pactum: dark label "LIVE ACTIVITY", dot indicator, scrollable event list
   - `ActivityEvent` type: `{ id, timestamp, label, status: 'ok' | 'warn' | 'info' | 'loading' }`
   - Renders permit check results (✅ / 🟡 / ℹ️) + loading rows
3. Add `"viewing"` to `IntakeScreen`'s `Step` union
4. In `handleParamsNext`: compute geometry, store in state, transition to `"viewing"`
5. Split-view when `step === "viewing"`:
   - `GlobeBackground` hidden via CSS class
   - Full-height flex row: `<HouseCanvas>` at `flex: 3`, `<ActivityFeed>` at `flex: 1`
   - `StepBar` stays at top
   - Modal card fades out via CSS opacity transition

**Risk:** R3F `<Canvas>` requires fixed-height container — split-view parent must have `height: 100vh` minus StepBar height.

---

## Phase 4C: POST /recommend Wiring
**Goal:** Fire the recommendation API when the viewer mounts, pipe results into the activity feed, store for Phase 5
**Effort:** ~1h

Steps:
1. Add `useState<Recommendation | null>` to `IntakeScreen`
2. In `handleParamsNext`: call `postRecommend(household!)` immediately on transition to "viewing"
3. Seed activity feed with `{ label: 'Solar wird berechnet...', status: 'loading' }`
4. On success: append `{ label: 'Empfehlung bereit — €X/Monat', status: 'ok' }`, store `Recommendation`
5. On error: append `{ label: 'Berechnung fehlgeschlagen', status: 'warn' }` + retry button
6. In DEV: default to `?fixture=demo-detached` so we get a real response without a running backend

**Risk:** `household` must be non-null when `handleParamsNext` fires (fixed in 4A). Add defensive guard.
