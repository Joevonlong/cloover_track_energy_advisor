// Phase 3 — two sub-steps matching the reference screenshots:
//   1. Roof type — visual card grid of roof type illustrations
//   2. Roof pitch — pitch preset cards + manual input
import { useState } from "react";

export interface RoofParams {
  roofType: "flat" | "gable" | "hip" | "shed";
  pitchDeg: number;
  wallHeightM: number;
}

interface RoofParamsStepProps {
  onBack(): void;
  onNext(params: RoofParams): void;
}

type SubStep = "type" | "pitch";

export default function RoofParamsStep({ onBack, onNext }: RoofParamsStepProps) {
  const [subStep, setSubStep] = useState<SubStep>("type");
  const [roofType, setRoofType] = useState<RoofParams["roofType"]>("gable");
  const [pitchPreset, setPitchPreset] = useState<number | "manual">(30);
  const [manualPitch, setManualPitch] = useState("");

  const effectivePitch =
    roofType === "flat" ? 0 : pitchPreset === "manual" ? Number(manualPitch) || 0 : pitchPreset;

  if (subStep === "type") {
    return (
      <CenteredCard>
        <h1 className="text-[28px] font-bold leading-tight tracking-[-0.02em] text-text-1">
          What type of roof do you have?
        </h1>
        <p className="mt-2 text-[15px] text-text-2">Please choose your roof type.</p>

        <div className="mt-10 grid grid-cols-4 gap-4">
          <RoofCard
            label="Gable roof"
            selected={roofType === "gable"}
            onClick={() => setRoofType("gable")}
            icon={<GableIcon />}
          />
          <RoofCard
            label="Hip roof"
            selected={roofType === "hip"}
            onClick={() => setRoofType("hip")}
            icon={<HipIcon />}
          />
          <RoofCard
            label="Flat roof"
            selected={roofType === "flat"}
            onClick={() => setRoofType("flat")}
            icon={<FlatIcon />}
          />
          <RoofCard
            label="Shed roof"
            selected={roofType === "shed"}
            onClick={() => setRoofType("shed")}
            icon={<ShedIcon />}
          />
        </div>

        <CardNav onBack={onBack} onNext={() => setSubStep("pitch")} nextDisabled={false} />
      </CenteredCard>
    );
  }

  const pitchCards: Array<{ value: number | "manual"; label: string }> = [
    { value: 0, label: "0°" },
    { value: 30, label: "30°" },
    { value: 45, label: "45°" },
    { value: "manual", label: "Manual" },
  ];

  const canProceed =
    roofType === "flat" ||
    (pitchPreset !== "manual" && pitchPreset > 0) ||
    (pitchPreset === "manual" && Number(manualPitch) > 0);

  return (
    <CenteredCard>
      <h1 className="text-[28px] font-bold leading-tight tracking-[-0.02em] text-text-1">
        What is the roof pitch?
      </h1>

      <div className="mt-8">
        <p className="mb-3 text-[13px] font-medium text-text-2">Roof pitch</p>
        <div className="grid grid-cols-4 gap-3">
          {pitchCards.map(({ value, label }) => {
            const active = pitchPreset === value;
            return (
              <button
                key={label}
                type="button"
                onClick={() => setPitchPreset(value)}
                className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 px-4 py-5 transition-colors duration-150 ${
                  active
                    ? "border-text-1 bg-white"
                    : "border-border bg-surface hover:border-border-strong"
                }`}
              >
                <div className="flex h-12 w-full items-center justify-center">
                  {value === 0 && <PitchIcon0 />}
                  {value === 30 && <PitchIcon30 />}
                  {value === 45 && <PitchIcon45 />}
                  {value === "manual" && (
                    <input
                      type="number"
                      placeholder="Angle°"
                      value={manualPitch}
                      onChange={(e) => setManualPitch(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full rounded-lg border border-border bg-white px-3 py-2 text-center text-[13px] text-text-1 outline-none focus:border-accent"
                    />
                  )}
                </div>
                {value !== "manual" && (
                  <span className={`text-[13px] font-medium ${active ? "text-text-1" : "text-text-3"}`}>
                    {label}
                  </span>
                )}
                {value === "manual" && (
                  <span className={`text-[13px] font-medium ${active ? "text-text-1" : "text-text-3"}`}>
                    {label}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <CardNav
        onBack={() => setSubStep("type")}
        onNext={() =>
          onNext({ roofType, pitchDeg: effectivePitch, wallHeightM: 3.0 })
        }
        nextDisabled={!canProceed}
      />
    </CenteredCard>
  );
}

// ─── Shared layout ────────────────────────────────────────────────────────────

function CenteredCard({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center px-6"
      style={{ paddingTop: 52 }}
    >
      <div
        className="pointer-events-auto w-full rounded-2xl bg-white px-12 py-10 font-sans"
        style={{
          maxWidth: 740,
          boxShadow: "0 24px 80px rgba(0,0,0,0.32), 0 2px 8px rgba(0,0,0,0.10)",
        }}
      >
        {children}
      </div>
    </div>
  );
}

function CardNav({
  onBack,
  onNext,
  nextDisabled,
}: {
  onBack(): void;
  onNext(): void;
  nextDisabled: boolean;
}) {
  return (
    <div className="mt-10 flex gap-4">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex h-12 w-36 items-center justify-center rounded-xl border border-border bg-surface text-[14px] font-semibold text-text-1 transition-[transform,filter] duration-150 ease-out-strong hover:bg-surface-2 active:scale-[0.97]"
      >
        Back
      </button>
      <button
        type="button"
        onClick={onNext}
        disabled={nextDisabled}
        className="inline-flex h-12 w-36 items-center justify-center rounded-xl bg-accent text-[14px] font-semibold text-white shadow-sm transition-[transform,filter] duration-150 ease-out-strong hover:brightness-95 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40"
      >
        Next
      </button>
    </div>
  );
}

// ─── Roof type cards ──────────────────────────────────────────────────────────

function RoofCard({
  label,
  selected,
  onClick,
  icon,
}: {
  label: string;
  selected: boolean;
  onClick(): void;
  icon: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-col items-center justify-end gap-3 rounded-xl border-2 pb-4 pt-6 transition-colors duration-150 ${
        selected
          ? "border-accent bg-accent-soft"
          : "border-border bg-white hover:border-border-strong hover:bg-surface"
      }`}
    >
      <div className="flex h-24 w-full items-end justify-center px-4">{icon}</div>
      <span className={`text-[12px] font-semibold ${selected ? "text-accent" : "text-text-2"}`}>
        {label}
      </span>
    </button>
  );
}

// ─── Roof type SVG icons (isometric 3/4 view) ─────────────────────────────────

function GableIcon() {
  return (
    <svg viewBox="0 0 110 80" className="w-full max-w-[110px]" fill="none">
      {/* front wall */}
      <polygon points="8,72 62,72 62,50 8,50" fill="#E5E5E5" />
      {/* right side wall */}
      <polygon points="62,72 86,62 86,40 62,50" fill="#CACACA" />
      {/* front gable triangle */}
      <polygon points="8,50 35,26 62,50" fill="#D8D8D8" />
      {/* right roof slope */}
      <polygon points="35,26 62,50 86,40 60,16" fill="#BEBEBE" />
    </svg>
  );
}

function HipIcon() {
  return (
    <svg viewBox="0 0 110 80" className="w-full max-w-[110px]" fill="none">
      {/* front wall */}
      <polygon points="8,72 62,72 62,50 8,50" fill="#E5E5E5" />
      {/* right side wall */}
      <polygon points="62,72 86,62 86,40 62,50" fill="#CACACA" />
      {/* front hip slope (trapezoid) */}
      <polygon points="8,50 20,34 50,34 62,50" fill="#D8D8D8" />
      {/* right hip slope */}
      <polygon points="50,34 62,50 86,40 74,28" fill="#BEBEBE" />
      {/* top ridge */}
      <line x1="20" y1="34" x2="50" y2="34" stroke="#ABABAB" strokeWidth="1" />
      <line x1="50" y1="34" x2="74" y2="28" stroke="#ABABAB" strokeWidth="1" />
    </svg>
  );
}

function FlatIcon() {
  return (
    <svg viewBox="0 0 110 80" className="w-full max-w-[110px]" fill="none">
      {/* front wall */}
      <polygon points="8,72 62,72 62,46 8,46" fill="#E5E5E5" />
      {/* right side wall */}
      <polygon points="62,72 86,62 86,36 62,46" fill="#CACACA" />
      {/* flat roof top */}
      <polygon points="4,44 8,46 62,46 86,36 82,34 28,34" fill="#D0D0D0" />
    </svg>
  );
}

function ShedIcon() {
  return (
    <svg viewBox="0 0 110 80" className="w-full max-w-[110px]" fill="none">
      {/* front wall (taller on left) */}
      <polygon points="8,72 62,72 62,52 8,40" fill="#E5E5E5" />
      {/* right side wall */}
      <polygon points="62,72 86,62 86,42 62,52" fill="#CACACA" />
      {/* shed roof slope */}
      <polygon points="4,38 8,40 62,52 86,42 82,40 28,28" fill="#D0D0D0" />
    </svg>
  );
}

// ─── Pitch SVG icons ──────────────────────────────────────────────────────────

function PitchIcon0() {
  return (
    <svg viewBox="0 0 80 40" className="w-16" fill="none">
      <line x1="10" y1="20" x2="70" y2="20" stroke="#6B7280" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function PitchIcon30() {
  return (
    <svg viewBox="0 0 80 50" className="w-16" fill="none">
      <polyline points="10,38 40,14 70,38" stroke="#9CA3AF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  );
}

function PitchIcon45() {
  return (
    <svg viewBox="0 0 80 60" className="w-16" fill="none">
      <polyline points="15,45 40,10 65,45" stroke="#9CA3AF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  );
}
