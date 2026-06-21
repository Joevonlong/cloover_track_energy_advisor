# Address-Based 3D Roof Builder

## Goal

Create a simple 3D house and roof model from an address plus a top-down satellite view.

This is not a photorealistic scan or automated reconstruction. The goal is to generate a clean building and roof shape so solar panels can be placed on realistic roof planes.

## Current Project Context

Already available:

- React frontend
- Three.js rendering
- React Three Fiber
- 3D scene and camera controls
- Panel placement logic
- Project saving with IndexedDB/localStorage
- Existing `.glb` model upload workflow

Currently missing:

- Address-to-map workflow
- Satellite roof view
- Manual roof outline drawing
- Simple generated 3D roof geometry

## Tech Stack To Add

- Google Geocoding API: converts address to latitude/longitude.
- Google Maps JavaScript API or Google Map Tiles API: displays satellite/top-down roof imagery.
- Drawing layer: lets the user click roof corners on the satellite image.
- Turf.js: converts map distances and bearings into real-world meters.
- Earcut: triangulates roof polygons for Three.js geometry when freeform roofs are added.

## Planned Flow

1. User enters an address.
2. App geocodes the address into latitude/longitude.
3. App shows satellite imagery centered on the roof.
4. User clicks roof corners manually.
5. User selects roof type:
   - flat
   - gable
   - hip
   - shed
6. User sets roof pitch and wall height.
7. App generates simple Three.js geometry:
   - walls
   - roof planes
   - panel placement surfaces
8. User places solar panels on the generated roof.
9. Project is saved like current projects.

## MVP Scope

First version should support:

- Address search
- Satellite view
- Manual rectangular roof outline
- Flat roof
- Gable roof
- Pitch slider
- Wall height setting
- Simple generated 3D model
- Panel placement on generated roof planes

Later versions can add:

- Freeform polygon roofs
- Hip roofs
- Shed roofs
- Multiple roof sections
- Obstacles like chimneys and skylights
- Better automatic roof detection

## MVP Architecture

### 1. Address Lookup

Use Google Geocoding API.

Input:

```ts
{
  address: string;
}
```

Output:

```ts
{
  formattedAddress: string;
  lat: number;
  lng: number;
}
```

Store the resolved address and coordinates in the project.

### 2. Satellite Tracing View

Use Google Maps JavaScript API with satellite map type.

The map should:

- Center on the resolved address.
- Zoom close enough for roof tracing.
- Let the user draw/edit a rectangular outline.
- Save the outline as `LatLng[]`.

For MVP, constrain drawing to four corners. This avoids the complexity of arbitrary polygons while still supporting many detached and semi-detached roofs.

### 3. Convert Outline To Meters

Keep the original map coordinates as the source of truth, then derive local Three.js coordinates from them.

Use Turf.js to calculate:

- Side lengths in meters.
- Roof orientation/bearing.
- Local 2D meter-space coordinates.

The generated model should use a local coordinate system centered around the roof footprint:

```ts
type LocalPoint = {
  x: number;
  z: number;
};
```

### 4. Generate Geometry

Flat roof:

- One raised rectangular roof plane.
- Four wall planes.
- One ground footprint/base.

Gable roof:

- Rectangular footprint.
- Ridge line through the long axis.
- Two sloped roof planes.
- Four wall faces, including triangular gable ends.

Pitch controls ridge height:

```ts
const ridgeHeight = Math.tan(pitchRadians) * (roofWidthM / 2);
const totalRoofHeight = wallHeightM + ridgeHeight;
```

### 5. Panel Placement Surfaces

Generated roof planes should become explicit panel-placement surfaces.

For a flat roof:

- One placement surface.

For a gable roof:

- Two placement surfaces.

Each surface should expose:

```ts
type RoofPlacementSurface = {
  id: string;
  roofType: "flat" | "gable";
  vertices: [number, number, number][];
  normal: [number, number, number];
  widthM: number;
  heightM: number;
  pitchDeg: number;
  azimuthDeg: number;
};
```

The existing panel placement logic should consume these generated surfaces the same way it consumes surfaces from uploaded `.glb` models.

### 6. Project Save Shape

Save generated-model parameters, not only raw geometry. This keeps the model editable after reload.

```ts
type GeneratedBuildingProject = {
  source: "address-generated";
  address: string;
  formattedAddress: string;
  lat: number;
  lng: number;
  outlineLatLng: { lat: number; lng: number }[];
  roofType: "flat" | "gable" | "hip" | "shed";
  pitchDeg: number;
  wallHeightM: number;
  generatedSurfaces: RoofPlacementSurface[];
  panels: unknown[];
};
```

## Key Caveats

- Satellite pixels are not meters. Always convert map coordinates into meter-space before building Three.js geometry.
- Bearing/orientation must be preserved so panels face the correct real-world direction.
- The first version should stay manual and rectangular. Automatic roof detection and freeform polygons can come later.
- Google API keys must stay in frontend-safe configuration where allowed, with usage restricted by domain and API restrictions.

## Recommended Implementation Order

1. Add address input and Google geocoding.
2. Add satellite map centered on the resolved address.
3. Add editable rectangular roof drawing.
4. Convert rectangle corners to local meter coordinates.
5. Generate flat roof geometry.
6. Generate gable roof geometry.
7. Connect generated roof planes to existing panel placement.
8. Save/load generated building projects.
