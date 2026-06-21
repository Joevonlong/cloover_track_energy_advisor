import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import mapboxgl from "mapbox-gl";

export interface GlobeHandle {
  flyTo: (lat: number, lon: number) => void;
  getMap: () => mapboxgl.Map | null;
}

interface GlobeBackgroundProps {
  revealed?: boolean;
  onZoomComplete?: () => void;
}

const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

const GlobeBackground = forwardRef<GlobeHandle, GlobeBackgroundProps>(function GlobeBackground(
  { onZoomComplete },
  ref,
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const pendingTargetRef = useRef<[number, number] | null>(null);
  const rotatingRef = useRef(true);
  const rafRef = useRef<number>(0);
  const onZoomCompleteRef = useRef(onZoomComplete);
  onZoomCompleteRef.current = onZoomComplete;

  function startRotation(map: mapboxgl.Map) {
    const spinStep = () => {
      if (!rotatingRef.current) return;
      const center = map.getCenter();
      center.lng -= 8; // degrees per step — one easeTo per second
      map.easeTo({ center, duration: 1000, easing: (t) => t });
    };
    map.on("moveend", spinStep);
    rafRef.current = 0; // unused now, kept for stopRotation compat
    // kick off the first step
    spinStep();
  }

  function stopRotation() {
    rotatingRef.current = false;
    // moveend listener stays but the guard above prevents further steps
  }

  function zoomTo(lat: number, lon: number) {
    const map = mapRef.current;
    if (!map) {
      pendingTargetRef.current = [lat, lon];
      return;
    }

    stopRotation();
    const center: [number, number] = [lon, lat];
    markerRef.current?.remove();
    markerRef.current = new mapboxgl.Marker({ color: "#d9f99d" }).setLngLat(center).addTo(map);
    // Include padding reset here so it's one atomic animation — a separate
    // easeTo call would cancel this flyTo before it could start.
    map.flyTo({
      center,
      zoom: 19,
      pitch: 0,
      bearing: 0,
      padding: { top: 0, right: 0, bottom: 0, left: 0 },
      speed: 2.5,
      curve: 1.2,
      essential: true,
    });
    map.once("moveend", () => {
      onZoomCompleteRef.current?.();
    });
  }

  useEffect(() => {
    if (!TOKEN || !containerRef.current || mapRef.current) return;

    // Canvas is always full-width. We use Mapbox padding to keep the globe
    // visually centered in the left portion while the form panel is visible.
    const panelW = Math.min(480, window.innerWidth * 0.38);

    mapboxgl.accessToken = TOKEN;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/satellite-streets-v12",
      center: [10.4515, 47.8],
      zoom: 1.75,
      pitch: 0,
      bearing: -12,
      projection: "globe",
      attributionControl: false,
    });
    map.setPadding({ top: 0, right: panelW, bottom: 0, left: 0 });
    map.addControl(new mapboxgl.AttributionControl({ compact: true }), "bottom-right");
    map.on("load", () => {
      map.setFog({
        color: "rgb(186, 210, 220)",
        "high-color": "rgb(36, 92, 120)",
        "horizon-blend": 0.08,
        "space-color": "rgb(4, 12, 16)",
        "star-intensity": 0.18,
      });
      startRotation(map);
      const target = pendingTargetRef.current;
      if (!target) return;
      pendingTargetRef.current = null;
      zoomTo(target[0], target[1]);
    });
    // Stop rotation while the user is dragging
    map.on("mousedown", stopRotation);
    mapRef.current = map;

    return () => {
      stopRotation();
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useImperativeHandle(ref, () => ({
    flyTo: (lat: number, lon: number) => {
      zoomTo(lat, lon);
    },
    getMap: () => mapRef.current,
  }));

  return (
    <div className="absolute inset-0 z-0 overflow-hidden bg-[#071014]">
      <div ref={containerRef} className="h-full w-full" />
      {!TOKEN ? (
        <div className="absolute inset-0 grid place-items-center bg-[#071014] text-[13px] font-medium text-white/70">
          Mapbox token missing
        </div>
      ) : null}
    </div>
  );
});

export default GlobeBackground;
