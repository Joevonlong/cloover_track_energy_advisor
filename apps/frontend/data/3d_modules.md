# Attachable 3D House Modules (toy layer)

A small visual gimmick on top of the generated house ([3d_building.md](./3d_building.md)).
Four energy products can be **toggled on/off**; when on, each appears in a **fixed,
predefined slot** on the house and plays a looping animation. Purely cosmetic — no money
math, no contract change. It only *reads* the house geometry and (optionally) the
recommendation to seed which toggles start on.

The four products are exactly the four rungs of the savings ladder
(`SelectionInput` in `src/lib/types.ts`), in order:

```
☀️ pv  →  🔋 battery  →  ♨️ heat_pump  →  🚗 ev
```

## Coordinate system (recap)

Local metre space, recentred on the footprint centroid (house sits at origin):

- `+x` = east, `+y` = up, `+z` = south.
- The footprint is an oriented rectangle with axes `u` (long / ridge axis) and
  `v` (short axis), half-extents `halfLong` (L) and `halfShort` (W).
- Modules anchor to `u` / `v` + `bounds`, **not** to world x/z, so they stay glued to
  the right wall even when the house is rotated to its real-world bearing.

`buildHouseGeometry()` exposes what modules need:

```ts
geometry.bounds   // { halfLongM, halfShortM, ridgeHeightM }
geometry.footprint// { u, v, halfLong, halfShort }   ← added for this layer
geometry.surfaces // RoofPlacementSurface[]           ← used by the solar panel
```

Wall height is the fixed `params.wallHeightM` (3.0 m today).

## Module catalog

Dimensions are real metres. Each module is built from plain `three` primitives
(`boxGeometry`, `cylinderGeometry`, `planeGeometry`) — **no new dependencies**.
Every module is rendered inside the existing `<House>` group, so it rises with the
extrude-up animation when the house first appears.

### ☀️ Solar panel — `pv`

| | |
|---|---|
| **Slot** | A **single panel** on the sun-facing roof plane, centred. Pitched roofs (gable/hip/shed): the plane whose `azimuthDeg` is closest to south (180°). Flat roof: laid on the roof top, tilted ~15° up toward south. |
| **Build** | One standard PV module **1.7 m × 1.0 m**, ~0.04 m thick, with a thin frame and a few cell grid-lines on the face. (One panel, not an array — duplicating into a grid is a possible later add.) |
| **Material** | Deep blue `#10243f`, low roughness (0.25) for a glassy look; light-grey frame `#9aa6b4`. |
| **Anchor data** | From `RoofPlacementSurface`: `vertices` (centroid), `normal`, `pitchDeg`, `azimuthDeg`. The panel lies in the plane, offset +0.05 m along `normal`. |
| **Animation** | Soft **emissive "glint"** sweeping diagonally across the glass (face `emissiveIntensity` pulsed by a moving highlight band). Subtle and glassy, not flashing. |

### ♨️ Heat pump — `heat_pump`

| | |
|---|---|
| **Slot** | On the ground, against the **long wall** on the `+v` (short-axis) side, pushed out ~0.8 m from the wall, near the `−u` end. Faces away from the house. |
| **Build** | Outdoor condenser box **1.0 m (w) × 0.9 m (h) × 0.4 m (d)** + a recessed circular **fan** (cylinder/disc, ~0.7 m ⌀) on the outward face, with simple radial blades. Small pipe stub into the wall. |
| **Material** | Off-white casing `#e8ebef`, dark fan housing `#2b3440`, steel blades `#cfd6de`. |
| **Anchor data** | Ground spot `(−0.35·L·u) + ((W + 0.8)·v)`, `y = 0`; rotated so the fan faces `+v`. |
| **Animation** | **Fan blades spin** continuously (~constant angular velocity). Plus a gentle **"pumping" pulse** — the housing breathes with a tiny `±2 %` vertical scale and the fan hub glows in a slow sine. Reads as "running". |

### 🔋 Battery — `battery`

| | |
|---|---|
| **Slot** | **Wall-mounted** on the gable end (the short wall at the `+u` end), centred, bottom edge ~0.6 m off the ground. |
| **Build** | Powerwall-style rounded slab **0.75 m (w) × 1.2 m (h) × 0.2 m (d)**. A vertical **charge-level bar** inset on the face, plus a thin **LED status strip** down one edge. |
| **Material** | Matte white shell `#f2f4f7`; charge bar emissive green `#34d27b`; LED strip emissive `#34d27b`. |
| **Anchor data** | On the `+u` wall: `(L·u) + (0·v)`, `y = 0.6 + 0.6`; flush to the wall, facing `+u`. |
| **Animation** | The **charge bar fills** from 0→100 % over ~3 s then holds, and the **LED strip pulses** slowly (emissive breathing). Suggests charging. |

### 🚗 EV charger — `ev`

| | |
|---|---|
| **Slot** | **Wall-mounted** on the front wall (the long wall on the `−v` side), near the `+u` corner — the "driveway" side. |
| **Build** | Compact wallbox **0.4 m (w) × 0.3 m (h) × 0.15 m (d)** with a glowing **LED ring** on the face and a thin curled **charging cable** (tube/curve) hanging to one side. (No car — kept clean; a parked-car prop is a possible later add.) |
| **Material** | Charcoal shell `#27313c`; LED ring emissive cyan `#46c8ff`; black cable `#1b1f24`. |
| **Anchor data** | On the `−v` wall near `+u`: `(0.6·L·u) − ((W)·v)`, `y = 1.1`; facing `−v`. |
| **Animation** | LED ring **breathing glow** (emissive sine) + a faint travelling dot around the ring. Reads as "ready / charging". |

## Toggle UX

- A floating chip bar over the `viewing` stage with four toggles: **☀️ Solar · 🔋 Battery ·
  ♨️ Heat pump · 🚗 EV charger**.
- State is a simple `{ pv, battery, heat_pump, ev }` boolean set held in `IntakeScreen`.
- Default: all **off** (user toggles them on to see them pop onto the house).
- Each newly-enabled module plays a short **drop/scale-in** before settling into its loop.

## Optional: seed toggles from the recommendation

The ladder is cumulative, so the recommended scenario implies a set of products. When a
`Recommendation` is present we *may* pre-enable the toggles up to the best rung:

| `best` is `alternatives[n]` | Pre-enabled modules |
|---|---|
| n = 0 | ☀️ |
| n = 1 | ☀️ 🔋 |
| n = 2 | ☀️ 🔋 ♨️ |
| n = 3 | ☀️ 🔋 ♨️ 🚗 |

(Match `best.scenario_id` to its position in `alternatives[]`.) This is a convenience seed
only — the user can still toggle anything on or off manually.

## Build notes / constraints

- **No new dependencies.** Everything is `three` primitives + `useFrame` animation inside
  react-three-fiber, which the viewer already uses.
- **No backend or contract change.** This layer never computes a number; it only reads
  `geometry` (always) and `Recommendation` (optional seed).
- Modules live in `src/features/viewer/houseModules.tsx`; anchor math lives next to the
  geometry in `src/features/viewer/roofGeometry.ts` (`moduleSlots()`), so placement stays in
  one place and scales with the drawn footprint.
- Keep animations **subtle and looping** — a slow glow/spin reads as "premium gimmick";
  fast flashing reads as broken.
