import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { useEffect, useRef, useState } from "react";
import type { Map as MapboxMap } from "mapbox-gl";

export interface LatLng {
  lat: number;
  lng: number;
}

// Custom draw theme. MapboxDraw defaults to orange (#fbb03b) while active, which
// fights the satellite imagery and the brand. Recolor to the accent blue with
// white-haloed vertices so corners stay legible over any roof. (emil-design-eng)
const DRAW_ACCENT = "#2f6fed";
const DRAW_STYLES = [
  {
    id: "gl-draw-polygon-fill",
    type: "fill",
    filter: ["all", ["==", "$type", "Polygon"]],
    paint: { "fill-color": DRAW_ACCENT, "fill-opacity": 0.14 },
  },
  {
    id: "gl-draw-polygon-stroke",
    type: "line",
    filter: ["all", ["==", "$type", "Polygon"]],
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": DRAW_ACCENT, "line-width": 2.5 },
  },
  {
    id: "gl-draw-line",
    type: "line",
    filter: ["all", ["==", "$type", "LineString"]],
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": DRAW_ACCENT, "line-width": 2.5, "line-dasharray": [0.4, 2] },
  },
  {
    id: "gl-draw-polygon-midpoint",
    type: "circle",
    filter: ["all", ["==", "$type", "Point"], ["==", "meta", "midpoint"]],
    paint: { "circle-radius": 3.5, "circle-color": DRAW_ACCENT },
  },
  {
    id: "gl-draw-vertex-halo",
    type: "circle",
    filter: ["all", ["==", "meta", "vertex"], ["==", "$type", "Point"]],
    paint: {
      "circle-radius": 6.5,
      "circle-color": "#ffffff",
      "circle-stroke-width": 1,
      "circle-stroke-color": "rgba(17,24,39,0.25)",
    },
  },
  {
    id: "gl-draw-vertex",
    type: "circle",
    filter: ["all", ["==", "meta", "vertex"], ["==", "$type", "Point"]],
    paint: { "circle-radius": 4, "circle-color": DRAW_ACCENT },
  },
];

export function useMapboxDraw(map: MapboxMap | null) {
  const drawRef = useRef<InstanceType<typeof MapboxDraw> | null>(null);
  const [polygon, setPolygon] = useState<LatLng[] | null>(null);

  useEffect(() => {
    if (!map) return;

    const draw = new MapboxDraw({ displayControlsDefault: false, styles: DRAW_STYLES });
    map.addControl(draw);
    draw.changeMode("draw_polygon");
    drawRef.current = draw;

    function capture() {
      const feat = draw.getAll().features[0];
      if (!feat) return;
      const ring = (feat.geometry as GeoJSON.Polygon).coordinates[0];
      setPolygon(ring.slice(0, -1).map(([lng, lat]) => ({ lat, lng })));
    }

    // Re-enter draw mode if Escape is pressed mid-draw (modechange fires with
    // no completed features). Guard against the re-entry itself triggering a loop.
    function onModeChange() {
      if (draw.getMode() === "draw_polygon") return;
      if (draw.getAll().features.length === 0) {
        draw.changeMode("draw_polygon");
      }
    }

    map.on("draw.create", capture);
    map.on("draw.update", capture);
    map.on("draw.modechange", onModeChange);

    return () => {
      map.off("draw.create", capture);
      map.off("draw.update", capture);
      map.off("draw.modechange", onModeChange);
      if (map.hasControl(draw)) map.removeControl(draw);
      drawRef.current = null;
      setPolygon(null);
    };
  }, [map]);

  function reset() {
    drawRef.current?.deleteAll();
    drawRef.current?.changeMode("draw_polygon");
    setPolygon(null);
  }

  return { polygon, reset };
}
