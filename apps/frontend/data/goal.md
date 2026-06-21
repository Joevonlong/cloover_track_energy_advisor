# Frontend Goal — Phase-by-Phase User Journey

The full flow from address input to interactive 3D recommendation view.

---

## [x] Phase 1 — Address Input & Map Zoom

User enters their address in the intake form (Mapbox autocomplete).

On confirmation the map executes a **cinematic camera flight**: zooms from street level down to a near-overhead satellite view (zoom ~19, pitch ~0). The transition takes ~2 seconds using Mapbox's default flyTo easing. The intake form disappears during or immediately after the flight.

**Implementation:**
```ts
map.flyTo({
  center: [lng, lat],
  zoom: 19,
  pitch: 0,
  bearing: 0,
  duration: 2200,
  essential: true,
});
map.once('moveend', () => showRoofDrawStep());
```

---

## [x] Phase 2 — Roof Drawing Step ("Zeichne dein Dach auf die Karte")

**After the zoom completes**, a modal card slides/fades in over a full-screen house background photo.

### Visual layout

```
┌──────────────────────────────────────────────────────┐
│  [full-screen house background photo]                │
│                                                      │
│   ┌──────────────────────────────────────────────┐   │
│   │   Zeichne dein Dach auf die Karte            │   │
│   │   Klicken Sie auf das Polygon-Werkzeug und   │   │
│   │   dann auf die Ecken Ihres Daches.           │   │
│   │                                              │   │
│   │  ┌────────────────────────────────────────┐  │   │
│   │  │ [Satellit] [Karte]                     │  │   │
│   │  │                                        │  │   │
│   │  │   embedded Mapbox satellite view       │  │   │
│   │  │   centered on user's address           │  │   │
│   │  │   zoom ~19, pitch 0                    │  │   │
│   │  │                                        │  │   │
│   │  └────────────────────────────────────────┘  │   │
│   │                                              │   │
│   │  [Zurück]      [Weiter ░]      [Überspringen]│   │
│   └──────────────────────────────────────────────┘   │
│                                          [Chat 💬]   │
└──────────────────────────────────────────────────────┘
```

### Component details

**Modal card**
- Centered white card, rounded corners (`rounded-2xl`), soft shadow
- Background behind card: full-screen house hero photo (static asset, blurred slightly)
- Title: bold dark heading — "Zeichne dein Dach auf die Karte"
- Subtitle: gray instruction text — polygon tool usage hint

**Embedded map**
- Mapbox GL JS instance mounted inside the card (not full-screen)
- Starts in satellite mode: `mapbox://styles/mapbox/satellite-v9`
- Toggle tabs top-left of the map: **Satellit** / **Karte** — switching changes the map style
- Map is pre-centered on the geocoded `[lng, lat]` at zoom ~19

**Polygon drawing tool**
- Use `@mapbox/mapbox-gl-draw` plugin
- Mode: `draw_polygon` — user clicks each roof corner, double-clicks to close
- Drawn polygon is highlighted on the map (white outline, semi-transparent fill)
- Stores result as `{ lat: number; lng: number }[]` (LatLng array per `3d_building.md`)

**Navigation buttons**
- **Zurück** — goes back to the intake form; ghost/outlined style
- **Weiter** — advances to Phase 3; **disabled and grayed out** until `draw.getAll().features.length > 0` (i.e. a polygon has been drawn)
- **Überspringen** — skip this step entirely; proceeds with no roof polygon (engine falls back to Google Solar API roof data only)

**Chat widget** (bottom-right corner)
- Small floating button with chat icon
- Expands to: "Haben Sie Fragen? Ich helfe Ihnen gerne weiter."
- Positioned fixed, always visible across all phases

### What fires in the background during this phase

The moment the roof drawing step appears, kick off background work:
- **Permit stream** starts: `GET /api/v1/advisor/permits/stream` (needs address + PLZ only)
- **Resolver** fetches PricingContext for the PLZ (electricity price, grid fee, irradiance)
- Right-panel activity feed shows permit checks ticking in live

By the time the user finishes drawing (~30–90 seconds), most permit checks are already done.

### Packages needed
```
@mapbox/mapbox-gl-draw   # polygon drawing on Mapbox
@turf/turf               # convert LatLng corners → real-world meters
```

---

## [x] Phase 3 — Roof Type & Parameters

After "Weiter", a second step (or a panel overlay on the same card) collects:

- **Roof type**: flat / gable *(MVP)* — hip / shed later (segmented control)
- **Pitch**: slider 0°–60°, default 30°
- **Wall height**: slider 2.5m–5m, default 3m

These plus the polygon coordinates are the complete input to the geometry generator.

---

## [ ] Phase 4 — 3D Model Generation (The Wow Moment)

The modal closes. The satellite map **folds up** into a 3D model: the polygon extrudes into walls and the chosen roof type rises into place (Three.js animation, ~1s).

Full-screen split view becomes active:

```
┌─────────────────────────────────┬───────────────────┐
│                                 │  LIVE ACTIVITY    │
│   Three.js canvas               │                   │
│   React Three Fiber             │  ✅ Permit checks  │
│                                 │  ✅ Denkmal check  │
│   [clean 3D house model]        │  ⏳ Solar calc...  │
│                                 │                   │
└─────────────────────────────────┴───────────────────┘
```

**Geometry generation** (see `3d_building.md` for full spec):
1. Polygon LatLng → Turf.js → local meter-space `{ x, z }[]`
2. Flat roof: one raised plane + four walls + ground base
3. Gable roof: ridge through long axis, two sloped planes, triangular gable ends
4. Ridge height: `Math.tan(pitchRad) * (widthM / 2)`
5. Each roof plane becomes a `RoofPlacementSurface` — consumed by existing panel placement logic

Solar layer fires now (needs roof area + pitch + azimuth). Backend computes Budget / Balanced / Max Independence offers.

---

## [ ] Phase 5 — Recommendations & Interactive 3D Components

When the backend response arrives, the house model becomes a configurator.

**Components animate onto the house per tier:**

| Component | 3D position |
|-----------|-------------|
| Solar panels | Roof planes (existing panel placement logic) |
| Heat pump | Exterior side wall |
| Battery | Garage / interior wall |
| EV charger | Driveway / garage wall |

**Three tiers** (F27 strategies), switchable via tabs above or beside the canvas:

| Tab | Strategy | Components shown |
|-----|----------|-----------------|
| Fastest payback | Solar + heat pump | Panels + heat pump |
| Best cost ratio *(default)* | Optimal full bundle | Panels + battery + heat pump + EV charger |
| Long-term | Max kWp + large battery | Full bundle, oversized |

Switching tiers animates components in/out. The user sees exactly what changes without reading a table.

**Hover on any component** shows a details card:
- Solar panels → "4.8 kWp · 12 panels · saves €68/mo"
- Heat pump → "SCOP 4.1 · replaces gas boiler · saves €45/mo"
- Battery → "8 kWh · autarky 30% → 70% · saves €X/mo"
- EV charger → "Home charging · saves €133/mo vs petrol"

Numbers come directly from `ScenarioResult.breakdown` — no separate data needed.

**The 3D canvas IS the dashboard.** No separate results screen.

---

## [ ] Right Panel — Live Activity Feed

Always showing something. Never an empty loading state.

| Phase | Right panel content |
|-------|-------------------|
| 2–3 (drawing) | Permit checks streaming in live (12 checks, one by one with ✅/🟡/ℹ️) |
| 4 (model gen) | "Analyzing your solar potential..." · location stats (irradiance, grid fee) |
| 5 (results) | Three strategy tier cards · €/month headline · "Subsidies verified X days ago" chip |

---

## Complete Flow Summary

```
Intake form (address + household data)
  → [Mapbox flyTo, ~2s cinematic zoom to rooftop]
  → Roof drawing modal appears over house background photo
      → User draws polygon over roof
      → Permits stream in background (right panel)
  → Roof type + pitch controls
  → [Modal closes, polygon folds into 3D model, ~1s animation]
  → Solar layer fires (needs geometry)
  → Split view: 3D canvas left / live activity right
      → Components animate onto house per tier
      → Tier tabs switch component combination
      → Hover shows per-component €/mo detail
```

---

## Implementation Checklist

### Phase 1 — Address Input & Map Zoom
- [x] Extend `lib/mapbox-geocode.ts` with `flyToAddress(map, lat, lng)` using `map.flyTo()`
- [x] Trigger `flyToAddress` on intake form confirmation
- [x] Hide intake form during / after zoom animation
- [x] Fire `showRoofDrawStep()` on `map.once('moveend')`

### Phase 2 — Roof Drawing Modal
- [x] Create `features/roof/RoofDrawStep.tsx` — modal card layout
- [x] Full-screen house background photo behind the card
- [x] Embed Mapbox GL map inside the card (not full-screen), pre-centered on address
- [x] Satellit / Karte toggle — switches map style between satellite and streets
- [x] Install `@mapbox/mapbox-gl-draw` and add polygon draw mode
- [x] Create `features/roof/useMapboxDraw.ts` — init draw, track polygon state, return `LatLng[]`
- [x] "Weiter" button disabled until polygon has ≥ 3 vertices
- [x] "Zurück" button — returns to intake form
- [x] "Überspringen" button — skips to Phase 4 with no polygon (falls back to Google Solar data)
- [x] Chat widget component (bottom-right fixed, expandable)
- [x] Start permit SSE stream (`GET /api/v1/advisor/permits/stream`) in the background when this step mounts
- [x] Install `@turf/turf` for coordinate conversion

### Phase 3 — Roof Parameters
- [x] Create `features/roof/RoofParamsStep.tsx`
- [x] Roof type selector: flat / gable (segmented control; hip / shed later)
- [x] Pitch slider: 0°–60°, default 30°
- [x] Wall height slider: 2.5m–5m, default 3m

### Phase 4 — 3D Model Generation
- [ ] Create `features/viewer/useRoofGeometry.ts` — `LatLng[] + params → Three.js BufferGeometry`
  - [ ] Turf.js: polygon LatLng → local meter-space `{ x, z }[]`
  - [ ] Flat roof geometry (plane + 4 walls + base)
  - [ ] Gable roof geometry (2 sloped planes + triangular gable ends)
  - [ ] Export `RoofPlacementSurface[]` per `3d_building.md` spec
- [ ] Create `features/viewer/HouseCanvas.tsx` — React Three Fiber scene
  - [ ] Animate polygon "folding up" into 3D model on mount (~1s)
  - [ ] Soft ambient lighting + ground plane
  - [ ] Orbit controls (mouse drag to rotate/inspect)
- [ ] Split-view layout: canvas left (~75%), activity feed right (~25%)
- [ ] Fire solar layer request when geometry is confirmed

### Phase 5 — Interactive Components & Tier Switching
- [ ] Create `features/viewer/components/SolarPanels.tsx` — panels on roof plane surfaces
- [ ] Create `features/viewer/components/HeatPump.tsx` — exterior side wall mount
- [ ] Create `features/viewer/components/Battery.tsx` — garage / interior wall
- [ ] Create `features/viewer/components/EvCharger.tsx` — driveway / garage wall
- [ ] Animate components in/out when they become active (fade or slide)
- [ ] Create `features/viewer/TierSwitcher.tsx` — tab control above canvas
  - [ ] "Fastest payback" tab → show panels + heat pump
  - [ ] "Best cost ratio" tab (default) → show all four components
  - [ ] "Long-term" tab → all components, max kWp variant
- [ ] Hover interaction on each component → show detail card (`€/mo`, specs, savings)
- [ ] Wire detail card numbers from `ScenarioResult.breakdown`

### Right Panel — Activity Feed
- [ ] Create `features/activity/ActivityFeed.tsx`
- [ ] Consume permit SSE stream, render checks as they arrive (✅ / 🟡 / ℹ️)
- [ ] Transition from permit list → "Analyzing solar potential..." spinner
- [ ] Render three strategy tier cards once recommendation response arrives
- [ ] "Subsidies verified X days ago" chip at bottom of panel

### Packages to Install
- [ ] `@mapbox/mapbox-gl-draw`
- [ ] `@turf/turf`
