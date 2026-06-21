// Phase 4B — R3F canvas. Renders the generated house with a soft extrude-up
// animation, a ground plane, lighting and orbit controls. Pure presentation:
// geometry comes pre-built from buildHouseGeometry().
import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { LatLng } from "@/features/roof/useMapboxDraw";
import type { RoofParams } from "@/features/roof/RoofParamsStep";
import { buildHouseGeometry } from "@/features/viewer/roofGeometry";

function House({ geometries }: { geometries: THREE.BufferGeometry[] }) {
  const group = useRef<THREE.Group>(null);

  // Extrude-up: lerp the group's vertical scale 0 → 1 over ~1s.
  useFrame((_, delta) => {
    const g = group.current;
    if (!g) return;
    if (g.scale.y < 1) {
      g.scale.y = Math.min(1, g.scale.y + delta * 1.4);
    }
  });

  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: "#d8dde2",
        roughness: 0.85,
        metalness: 0.0,
        side: THREE.DoubleSide,
      }),
    [],
  );

  return (
    <group ref={group} scale={[1, 0.001, 1]}>
      {geometries.map((geo, i) => (
        <mesh key={i} geometry={geo} material={material} castShadow receiveShadow />
      ))}
    </group>
  );
}

export interface HouseCanvasProps {
  polygon: LatLng[] | null;
  params: RoofParams;
}

export default function HouseCanvas({ polygon, params }: HouseCanvasProps) {
  const { geometries, bounds } = useMemo(
    () => buildHouseGeometry(polygon, params),
    [polygon, params],
  );

  // Frame the camera relative to the footprint size.
  const reach = Math.max(bounds.halfLongM, bounds.halfShortM, 4);
  const camPos: [number, number, number] = [reach * 1.4, reach * 1.1, reach * 1.9];

  return (
    <Canvas
      shadows
      camera={{ fov: 45, position: camPos, near: 0.1, far: 200 }}
      dpr={[1, 2]}
      gl={{ antialias: true }}
    >
      <color attach="background" args={["#0a1c22"]} />
      <fog attach="fog" args={["#0a1c22", reach * 3, reach * 9]} />

      <ambientLight intensity={0.5} />
      <directionalLight
        position={[reach, reach * 2, reach]}
        intensity={1.4}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />

      {/* Ground plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[reach * 8, reach * 8]} />
        <meshStandardMaterial color="#0e2026" roughness={1} />
      </mesh>

      <House geometries={geometries} />

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minDistance={reach}
        maxDistance={reach * 6}
        maxPolarAngle={Math.PI / 2.05}
        target={[0, bounds.ridgeHeightM * 0.5 + 1.5, 0]}
      />
    </Canvas>
  );
}
