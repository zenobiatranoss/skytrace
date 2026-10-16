import { useEffect } from "react";
import maplibregl from "maplibre-gl";

import type { Track } from "../../types/flight";

const SOURCE_ID = "selected-track";
const LINE_ID = "selected-track-line";

function toGeoJson(track: Track | null): GeoJSON.Feature<GeoJSON.LineString> {
  const coordinates = (track?.points ?? []).map(
    (point) => [point.longitude, point.latitude] as [number, number],
  );

  return {
    type: "Feature",
    properties: {},
    geometry: { type: "LineString", coordinates },
  };
}

// draws the path we actually observed for the selected aircraft. a straight
// line between two airports would be a lie, so we don't do that here.
export function FlightPath({ map, track }: { map: maplibregl.Map; track: Track | null }) {
  useEffect(() => {
    const data = toGeoJson(track);
    const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

    if (!source) {
      map.addSource(SOURCE_ID, { type: "geojson", data });
      map.addLayer({
        id: LINE_ID,
        type: "line",
        source: SOURCE_ID,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#38bdf8",
          "line-width": 2.5,
          "line-opacity": 0.85,
        },
      });
    } else {
      source.setData(data);
    }
  }, [map, track]);

  useEffect(() => {
    return () => {
      if (map.getLayer(LINE_ID)) map.removeLayer(LINE_ID);
      if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
    };
  }, [map]);

  return null;
}
