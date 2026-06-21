// Intake screen. Step flow:
//   intake → zooming → roof-draw → roof-params → viewing (3D model + feed)
import { useRef, useState } from "react";
import type { Map as MapboxMap } from "mapbox-gl";
import GlobeBackground, { type GlobeHandle } from "@/components/globe-background";
import StepBar from "@/components/StepBar";
import IntakeForm from "@/features/intake/IntakeForm";
import RoofDrawStep from "@/features/roof/RoofDrawStep";
import RoofParamsStep, { type RoofParams } from "@/features/roof/RoofParamsStep";
import HouseCanvas from "@/features/viewer/HouseCanvas";
import ActivityFeed, { type ActivityEvent } from "@/features/activity/ActivityFeed";
import type { LatLng } from "@/features/roof/useMapboxDraw";
import { postRecommend } from "@/lib/api";
import type { Household, Recommendation } from "@/lib/types";

export interface IntakeScreenProps {
  onComplete?: (household: Household) => void;
}

type Step = "intake" | "zooming" | "roof-draw" | "roof-params" | "viewing";

// Maps each step to the StepBar index (0 = Address, 1 = Roof, 2 = Parameters, 3 = Model).
const STEP_INDEX: Record<Step, number> = {
  intake: 0,
  zooming: 0,
  "roof-draw": 1,
  "roof-params": 2,
  viewing: 3,
};

// Short clock label for activity rows. Stable & dependency-free.
function clock(): string {
  return new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
}

let eventSeq = 0;
function makeEvent(label: string, status: ActivityEvent["status"]): ActivityEvent {
  return { id: `ev-${eventSeq++}`, timestamp: clock(), label, status };
}

export default function IntakeScreen({ onComplete }: IntakeScreenProps) {
  const globeRef = useRef<GlobeHandle>(null);
  const [step, setStep] = useState<Step>("intake");
  const [roofMap, setRoofMap] = useState<MapboxMap | null>(null);
  const [polygon, setPolygon] = useState<LatLng[] | null>(null);
  const [household, setHousehold] = useState<Household | null>(null);
  const [params, setParams] = useState<RoofParams | null>(null);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [, setRecommendation] = useState<Recommendation | null>(null);

  const handleHousehold = (h: Household) => {
    setHousehold(h);
    onComplete?.(h);
  };

  const handleAddressPick = (lat: number, lon: number) => {
    if (import.meta.env.DEV) {
      (window as unknown as { __pick?: unknown }).__pick = { lat, lon };
    }
    globeRef.current?.flyTo(lat, lon);
    setStep("zooming");
  };

  const handleZoomComplete = () => {
    setRoofMap(globeRef.current?.getMap() ?? null);
    setStep("roof-draw");
  };

  const handleDrawNext = (poly: LatLng[]) => {
    setPolygon(poly);
    setStep("roof-params");
  };

  const handleDrawSkip = () => {
    setPolygon(null);
    setStep("roof-params");
  };

  // Kick off the recommendation request and stream progress into the feed (4C).
  const runRecommend = (h: Household) => {
    setEvents([makeEvent("Solar wird berechnet…", "loading")]);
    // In DEV, use a golden fixture so we don't need a running backend.
    const opts = import.meta.env.DEV ? { fixture: "demo-detached" } : undefined;
    postRecommend(h, opts)
      .then((rec) => {
        setRecommendation(rec);
        const eur = Math.round(rec.best.monthly_saving_eur);
        setEvents((prev) => [
          ...prev.map((e) => (e.status === "loading" ? { ...e, status: "ok" as const } : e)),
          makeEvent(`Empfehlung bereit — €${eur}/Monat`, "ok"),
        ]);
      })
      .catch(() => {
        setEvents((prev) => [
          ...prev.map((e) => (e.status === "loading" ? { ...e, status: "warn" as const } : e)),
          makeEvent("Berechnung fehlgeschlagen", "warn"),
        ]);
      });
  };

  const handleParamsNext = (p: RoofParams) => {
    setParams(p);
    setStep("viewing");
    if (household) {
      runRecommend(household);
    } else {
      // Defensive: household should be set from the intake form. Surface the gap
      // in the feed rather than firing /recommend with no body.
      setEvents([makeEvent("Haushaltsdaten fehlen — bitte erneut starten", "warn")]);
    }
  };

  const formHidden = step !== "intake";

  return (
    <main className="intake-screen">
      <GlobeBackground ref={globeRef} onZoomComplete={handleZoomComplete} />
      <StepBar currentStep={STEP_INDEX[step]} />

      <div className={`intake-form-col${formHidden ? " intake-form-col--revealed" : ""}`}>
        <IntakeForm onComplete={handleHousehold} onAddressPick={handleAddressPick} />
      </div>

      {step === "roof-draw" && (
        <RoofDrawStep
          map={roofMap}
          onBack={() => setStep("intake")}
          onNext={handleDrawNext}
          onSkip={handleDrawSkip}
        />
      )}

      {step === "roof-params" && (
        <RoofParamsStep onBack={() => setStep("roof-draw")} onNext={handleParamsNext} />
      )}

      {step === "viewing" && params && (
        <div className="viewer-split">
          <div className="viewer-stage">
            <HouseCanvas polygon={polygon} params={params} />
          </div>
          <div className="viewer-feed">
            <ActivityFeed events={events} />
          </div>
        </div>
      )}
    </main>
  );
}
