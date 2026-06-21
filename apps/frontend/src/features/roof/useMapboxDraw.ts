import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { useEffect, useRef, useState } from "react";
import type { Map as MapboxMap } from "mapbox-gl";

export interface LatLng {
  lat: number;
  lng: number;
}

export function useMapboxDraw(map: MapboxMap | null) {
  const drawRef = useRef<InstanceType<typeof MapboxDraw> | null>(null);
  const [polygon, setPolygon] = useState<LatLng[] | null>(null);

  useEffect(() => {
    if (!map) return;

    const draw = new MapboxDraw({ displayControlsDefault: false });
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
