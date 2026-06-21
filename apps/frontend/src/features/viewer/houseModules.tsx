// Toy module layer — the four toggleable energy props (☀️ pv, 🔋 battery,
// ♨️ heat_pump, 🚗 ev) attached to the generated house. Pure presentation:
// anchors come from moduleSlots() in roofGeometry.ts. Spec: data/3d_modules.md.
//
// Phase 1: every kind renders a labelled placeholder box at its slot so we can
// verify anchoring across roof types before modelling the real props (Phase 2).
import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { ModuleKind, ModuleSlot } from "@/features/viewer/roofGeometry";

const UP = new THREE.Vector3(0, 1, 0);

// Placeholder swatch + rough size (metres) per kind — replaced in Phase 2.
const PLACEHOLDER: Record<ModuleKind, { color: string; size: [number, number, number] }> = {
  pv: { color: "#10243f", size: [1.7, 0.04, 1.0] },
  battery: { color: "#34d27b", size: [0.75, 1.2, 0.2] },
  heat_pump: { color: "#2b3440", size: [1.0, 0.9, 0.4] },
  ev: { color: "#46c8ff", size: [0.4, 0.3, 0.15] },
};

/**
 * One attached module. Positions/rotates to the slot, plays a short drop +
 * scale-in on mount, then holds. For roof-mounted `pv` the group is tilted so
 * its local +y aligns with the roof-surface normal.
 */
export default function HouseModule({ slot }: { slot: ModuleSlot }) {
  const group = useRef<THREE.Group>(null);
  const t = useRef(0); // mount progress seconds

  // Tilt quaternion for roof-mounted modules (pv): map +y → surface normal.
  const tilt = useRef<THREE.Quaternion | null>(null);
  if (slot.surface && tilt.current === null) {
    const n = new THREE.Vector3(...slot.surface.normal).normalize();
    tilt.current = new THREE.Quaternion().setFromUnitVectors(UP, n);
  }

  useFrame((_, delta) => {
    const g = group.current;
    if (!g) return;
    if (t.current < 1) {
      t.current = Math.min(1, t.current + delta * 2.2); // ~0.45 s
      const e = 1 - Math.pow(1 - t.current, 3); // ease-out cubic
      g.scale.setScalar(e);
      g.position.y = slot.position[1] + (1 - e) * 0.6; // drop into place
    }
  });

  return (
    <group
      ref={group}
      position={slot.position}
      rotation={[0, slot.rotationY, 0]}
      scale={0.001}
    >
      <group quaternion={tilt.current ?? undefined}>
        <mesh castShadow receiveShadow>
          <boxGeometry args={PLACEHOLDER[slot.kind].size} />
          <meshStandardMaterial
            color={PLACEHOLDER[slot.kind].color}
            roughness={0.6}
            metalness={0}
          />
        </mesh>
      </group>
    </group>
  );
}
