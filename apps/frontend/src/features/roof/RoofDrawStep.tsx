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

  const ready = polygon != null;

  return (
    // pointer-events-none shell; only the bar itself re-enables events
    <div className="pointer-events-none absolute inset-0 z-10 flex flex-col justify-end p-5">
      <div
        className="roof-draw-panel pointer-events-auto w-full rounded-2xl bg-white font-sans"
        style={{
          boxShadow: "0 8px 40px rgba(0,0,0,0.28), 0 2px 8px rgba(0,0,0,0.12)",
          maxWidth: 820,
          margin: "0 auto",
        }}
      >
        <div className="flex items-center gap-4 px-5 py-3.5">
          {/* Lead: icon + title block */}
          <span
            className="grid h-8 w-8 shrink-0 place-items-center rounded-[10px] text-accent"
            style={{ background: "var(--accent-soft)" }}
            aria-hidden
          >
            <RoofGlyph />
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="text-[15px] font-bold leading-tight tracking-[-0.01em] text-text-1">
              Draw your roof on the map
            </h2>
            <p className="mt-px flex items-center gap-2 text-[12px] leading-snug text-text-2">
              <span
                className={`roof-dot ${ready ? "roof-dot--ready" : "roof-dot--waiting"}`}
              />
              <span className="tabular-nums">
                {ready
                  ? `${polygon.length} corners set · ready to continue`
                  : "Click each roof corner above, then double-click to finish"}
              </span>
            </p>
          </div>

          {/* Trailing: nav */}
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
            className="inline-flex h-9 shrink-0 items-center justify-center rounded-lg border border-border bg-white px-3.5 text-[13px] font-medium text-text-2 transition-[transform,background-color] duration-150 ease-out-strong hover:bg-surface active:scale-[0.97]"
          >
            Skip
          </button>

          <button
            type="button"
            onClick={() => polygon && onNext(polygon)}
            disabled={!ready}
            className="inline-flex h-9 shrink-0 items-center justify-center gap-1.5 rounded-lg bg-accent px-4 text-[13px] font-semibold text-white transition-[transform,filter,box-shadow] duration-150 ease-out-strong hover:brightness-105 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none enabled:[box-shadow:var(--shadow-accent)]"
          >
            Next
            <span aria-hidden>→</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// Roof outline with corner nodes — mirrors the "click each corner" gesture.
function RoofGlyph() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 11 L12 4.5 L20 11 L20 19.5 L4 19.5 Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <g fill="currentColor">
        <circle cx="4" cy="11" r="1.7" />
        <circle cx="12" cy="4.5" r="1.7" />
        <circle cx="20" cy="11" r="1.7" />
      </g>
    </svg>
  );
}
