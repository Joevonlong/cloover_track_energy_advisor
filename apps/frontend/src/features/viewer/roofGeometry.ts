// Phase 4A — Geometry engine.
// Pure module: (LatLng[] | null) + RoofParams → Three.js BufferGeometry[] +
// RoofPlacementSurface[]. No React, no DOM. Spec: data/3d_building.md.
//
// Coordinate system (local metre space, Three.js convention):
//   +x = east, +y = up, +z = south  (north = −z)
// The footprint is recentred on its own centroid, so the house sits at the
// world origin and the camera/orbit target can stay at (0,0,0).
import * as THREE from "three";
import { rhumbBearing, rhumbDistance } from "@turf/turf";
import type { LatLng } from "@/features/roof/useMapboxDraw";
import type { RoofParams } from "@/features/roof/RoofParamsStep";

type Vec3 = [number, number, number];

/** A placement surface a future panel-layout pass can consume (3d_building.md §5). */
export interface RoofPlacementSurface {
  id: string;
  roofType: "flat" | "gable";
  vertices: Vec3[];
  normal: Vec3;
  widthM: number;
  heightM: number;
  pitchDeg: number;
  azimuthDeg: number;
}

export interface HouseGeometry {
  /** Wall + roof meshes, ready to drop into a <mesh> each. */
  geometries: THREE.BufferGeometry[];
  /** Explicit roof planes for downstream panel placement. */
  surfaces: RoofPlacementSurface[];
  /** Footprint half-extents — handy for framing the camera. */
  bounds: { halfLongM: number; halfShortM: number; ridgeHeightM: number };
}

// ── Footprint ────────────────────────────────────────────────────────────────

/** An oriented rectangle in local metre space. u = long axis, v = short axis. */
interface Footprint {
  halfLong: number; // L: half-extent along u (ridge axis)
  halfShort: number; // W: half-extent along v
  u: { x: number; z: number }; // unit vector, long axis
  v: { x: number; z: number }; // unit vector, short axis
}

/** 10 m × 8 m rectangle, long axis pointing east — used when no polygon drawn. */
const DEFAULT_FOOTPRINT: Footprint = {
  halfLong: 5,
  halfShort: 4,
  u: { x: 1, z: 0 },
  v: { x: 0, z: 1 },
};

/**
 * Convert drawn lat/lng corners to local metre-space points, recentred on the
 * polygon centroid. Uses rhumb bearing + distance so real-world azimuth is
 * preserved (caveat in 3d_building.md): panels must face the right direction.
 */
export function latLngToLocal(polygon: LatLng[]): { x: number; z: number }[] {
  const lat0 = polygon.reduce((s, p) => s + p.lat, 0) / polygon.length;
  const lng0 = polygon.reduce((s, p) => s + p.lng, 0) / polygon.length;
  const origin = [lng0, lat0];

  return polygon.map((p) => {
    const dest = [p.lng, p.lat];
    const dist = rhumbDistance(origin, dest, { units: "meters" });
    const bearing = (rhumbBearing(origin, dest) * Math.PI) / 180; // clockwise from north
    const east = dist * Math.sin(bearing);
    const north = dist * Math.cos(bearing);
    return { x: east, z: -north }; // +z = south
  });
}

/** Oriented bounding rectangle of the local points; long axis becomes the ridge. */
function orientedFootprint(localPts: { x: number; z: number }[]): Footprint {
  // Long axis = direction of the polygon's longest edge.
  let best = { len: -1, dx: 1, dz: 0 };
  for (let i = 0; i < localPts.length; i++) {
    const a = localPts[i];
    const b = localPts[(i + 1) % localPts.length];
    const dx = b.x - a.x;
    const dz = b.z - a.z;
    const len = Math.hypot(dx, dz);
    if (len > best.len) best = { len, dx, dz };
  }
  let u = { x: best.dx / best.len, z: best.dz / best.len };
  let v = { x: -u.z, z: u.x };

  // Project every point onto u/v to get extents.
  const proj = (axis: { x: number; z: number }) => {
    let min = Infinity;
    let max = -Infinity;
    for (const p of localPts) {
      const d = p.x * axis.x + p.z * axis.z;
      if (d < min) min = d;
      if (d > max) max = d;
    }
    return (max - min) / 2;
  };
  let halfLong = proj(u);
  let halfShort = proj(v);

  // Guarantee u is the longer axis so the ridge runs lengthwise.
  if (halfShort > halfLong) {
    [u, v] = [v, u];
    [halfLong, halfShort] = [halfShort, halfLong];
  }
  return { halfLong, halfShort, u, v };
}

// ── Face helpers ──────────────────────────────────────────────────────────────

/** Fan-triangulate a convex planar polygon into a BufferGeometry. */
function faceGeometry(verts: Vec3[]): THREE.BufferGeometry {
  const positions: number[] = [];
  for (let i = 1; i < verts.length - 1; i++) {
    positions.push(...verts[0], ...verts[i], ...verts[i + 1]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  g.computeVertexNormals();
  return g;
}

function faceNormal(a: Vec3, b: Vec3, c: Vec3): Vec3 {
  const ab = new THREE.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
  const ac = new THREE.Vector3(c[0] - a[0], c[1] - a[1], c[2] - a[2]);
  const n = ab.cross(ac).normalize();
  return [n.x, n.y, n.z];
}

/** Compass bearing (deg from north, clockwise) of a local (x,z) direction. */
function bearingDeg(dir: { x: number; z: number }): number {
  const deg = (Math.atan2(dir.x, -dir.z) * 180) / Math.PI;
  return (deg + 360) % 360;
}

/** The four footprint corners in local metre space, CCW. */
function corners(fp: Footprint): Vec3[] {
  const { u, v, halfLong: L, halfShort: W } = fp;
  const c = (su: number, sv: number): Vec3 => [
    su * L * u.x + sv * W * v.x,
    0,
    su * L * u.z + sv * W * v.z,
  ];
  return [c(+1, +1), c(-1, +1), c(-1, -1), c(+1, -1)];
}

/** Side walls: four vertical quads from ground to `topY` along each footprint edge. */
function wallGeometries(base: Vec3[], topY: number): THREE.BufferGeometry[] {
  return base.map((a, i) => {
    const b = base[(i + 1) % base.length];
    return faceGeometry([
      [a[0], 0, a[2]],
      [b[0], 0, b[2]],
      [b[0], topY, b[2]],
      [a[0], topY, a[2]],
    ]);
  });
}

// ── Roof builders ─────────────────────────────────────────────────────────────

function buildFlatRoof(fp: Footprint, wallHeightM: number): HouseGeometry {
  const base = corners(fp);
  const top = base.map<Vec3>(([x, , z]) => [x, wallHeightM, z]);
  const geometries = [...wallGeometries(base, wallHeightM), faceGeometry(top)];

  const surface: RoofPlacementSurface = {
    id: "flat-0",
    roofType: "flat",
    vertices: top,
    normal: [0, 1, 0],
    widthM: fp.halfLong * 2,
    heightM: fp.halfShort * 2,
    pitchDeg: 0,
    azimuthDeg: 180, // flat roof has no aspect; default south
  };
  return {
    geometries,
    surfaces: [surface],
    bounds: { halfLongM: fp.halfLong, halfShortM: fp.halfShort, ridgeHeightM: 0 },
  };
}

function buildGableRoof(
  fp: Footprint,
  wallHeightM: number,
  pitchDeg: number,
): HouseGeometry {
  const { u, v, halfLong: L, halfShort: W } = fp;
  const pitchRad = (pitchDeg * Math.PI) / 180;
  const ridgeHeight = Math.tan(pitchRad) * W; // roofWidthM/2 = W
  const ridgeY = wallHeightM + ridgeHeight;

  // Named local points.
  const p = (su: number, sv: number, y: number): Vec3 => [
    su * L * u.x + sv * W * v.x,
    y,
    su * L * u.z + sv * W * v.z,
  ];
  const eaveAplus = p(+1, +1, wallHeightM);
  const eaveAminus = p(-1, +1, wallHeightM);
  const eaveBplus = p(+1, -1, wallHeightM);
  const eaveBminus = p(-1, -1, wallHeightM);
  const ridgePlus = p(+1, 0, ridgeY); // u = +L end
  const ridgeMinus = p(-1, 0, ridgeY); // u = −L end

  const base = corners(fp);
  const geometries: THREE.BufferGeometry[] = [...wallGeometries(base, wallHeightM)];

  // Gable-end triangles on the two short walls (u = ±L).
  geometries.push(faceGeometry([eaveAplus, eaveBplus, ridgePlus]));
  geometries.push(faceGeometry([eaveBminus, eaveAminus, ridgeMinus]));

  // Two sloped roof planes.
  const planeA: Vec3[] = [eaveAminus, eaveAplus, ridgePlus, ridgeMinus]; // faces +v
  const planeB: Vec3[] = [eaveBplus, eaveBminus, ridgeMinus, ridgePlus]; // faces −v
  geometries.push(faceGeometry(planeA), faceGeometry(planeB));

  const slopeLen = Math.hypot(W, ridgeHeight);
  const surfaces: RoofPlacementSurface[] = [
    {
      id: "gable-0",
      roofType: "gable",
      vertices: planeA,
      normal: faceNormal(planeA[0], planeA[1], planeA[2]),
      widthM: L * 2,
      heightM: slopeLen,
      pitchDeg,
      azimuthDeg: bearingDeg(v),
    },
    {
      id: "gable-1",
      roofType: "gable",
      vertices: planeB,
      normal: faceNormal(planeB[0], planeB[1], planeB[2]),
      widthM: L * 2,
      heightM: slopeLen,
      pitchDeg,
      azimuthDeg: bearingDeg({ x: -v.x, z: -v.z }),
    },
  ];

  return {
    geometries,
    surfaces,
    bounds: { halfLongM: L, halfShortM: W, ridgeHeightM: ridgeHeight },
  };
}

// ── Dispatch ──────────────────────────────────────────────────────────────────

/**
 * Build the full house geometry from the (optional) drawn polygon + roof params.
 * hip/shed fall back to gable for the MVP (3d_building.md "Later versions").
 */
export function buildHouseGeometry(
  polygon: LatLng[] | null,
  params: RoofParams,
): HouseGeometry {
  const fp =
    polygon && polygon.length >= 3
      ? orientedFootprint(latLngToLocal(polygon))
      : DEFAULT_FOOTPRINT;

  if (params.roofType === "flat") {
    return buildFlatRoof(fp, params.wallHeightM);
  }
  // gable | hip | shed → gable geometry for MVP.
  return buildGableRoof(fp, params.wallHeightM, params.pitchDeg);
}
