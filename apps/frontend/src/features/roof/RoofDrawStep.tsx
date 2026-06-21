// Compact bottom bar floated over the full-screen satellite map.
// The house roof is fully visible above — the user draws directly on the map.
import type { Map as MapboxMap } from "mapbox-gl";
import { useMapboxDraw, type LatLng } from "./useMapboxDraw";

interface RoofDrawStepProps {
  map: MapboxMap | null;
  onBack(): void;
  onNext(polygon: LatLng[]): void;
  onSkip(): void;
}

export default function RoofDrawStep({ map, onBack, onNext, onSkip }: RoofDrawStepProps) {
  const { polygon, reset } = useMapboxDraw(map);

  function handleBack() {
    reset();
    onBack();
  }

  return (
    // pointer-events-none shell; only the bar itself re-enables events
    <div className="pointer-events-none absolute inset-0 z-10 flex flex-col justify-end p-5">
      <div
        className="pointer-events-auto w-full rounded-2xl bg-white font-sans"
        style={{
          boxShadow: "0 8px 40px rgba(0,0,0,0.28), 0 2px 8px rgba(0,0,0,0.12)",
          maxWidth: 820,
          margin: "0 auto",
        }}
      >
        {/* Title row */}
        <div className="border-b border-border px-6 py-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-3">
            Step 2
          </p>
          <h2 className="mt-0.5 text-[17px] font-bold leading-snug tracking-[-0.01em] text-text-1">
            Draw your roof on the map
          </h2>
          <p className="mt-0.5 text-[12px] leading-relaxed text-text-2">
            Click each roof corner above, then double-click to finish.
          </p>
        </div>

        {/* Status + nav row */}
        <div className="flex items-center gap-3 px-6 py-4">
          {/* Status chip */}
          <div
            className={`flex-1 rounded-lg border px-3.5 py-2.5 text-[13px] leading-snug transition-colors duration-200 ${
              polygon
                ? "border-[rgba(5,150,105,0.3)] bg-success-soft text-success"
                : "border-border bg-surface text-text-2"
            }`}
          >
            {polygon
              ? `✓ ${polygon.length} corner points - ready`
              : "No roof drawn yet"}
          </div>

          <button
            type="button"
            onClick={handleBack}
            className="shrink-0 text-[13px] font-medium text-text-2 transition-colors duration-150 ease-out-strong hover:text-text-1"
          >
            ← Back
          </button>

          <button
            type="button"
            onClick={onSkip}
            className="inline-flex h-10 shrink-0 items-center justify-center rounded-xl border border-border bg-white px-4 text-[13px] font-medium text-text-2 transition-[transform,filter] duration-150 ease-out-strong hover:bg-surface active:scale-[0.97]"
          >
            Skip
          </button>

          <button
            type="button"
            onClick={() => polygon && onNext(polygon)}
            disabled={!polygon}
            className="inline-flex h-10 shrink-0 items-center justify-center rounded-xl bg-accent px-5 text-[13px] font-semibold text-white shadow-sm transition-[transform,filter] duration-150 ease-out-strong hover:brightness-95 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
