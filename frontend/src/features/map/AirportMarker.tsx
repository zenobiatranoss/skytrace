import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

interface Props {
  map: maplibregl.Map;
  longitude: number;
  latitude: number;
  label?: string | null;
}

const AIRPORT_SVG =
  '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24">' +
  '<circle cx="12" cy="12" r="5" fill="none" stroke="#facc15" stroke-width="2.5"/>' +
  '<circle cx="12" cy="12" r="1.6" fill="#facc15"/></svg>';

export function AirportMarker({ map, longitude, latitude, label }: Props) {
  const markerRef = useRef<maplibregl.Marker | null>(null);

  useEffect(() => {
    const element = document.createElement("div");
    element.className = "airport-marker";
    element.style.width = "22px";
    element.style.height = "22px";
    element.style.backgroundImage = `url("data:image/svg+xml;charset=utf-8,${encodeURIComponent(AIRPORT_SVG)}")`;
    element.style.backgroundSize = "contain";
    if (label) element.title = label;

    const marker = new maplibregl.Marker({ element })
      .setLngLat([longitude, latitude])
      .addTo(map);

    markerRef.current = marker;
    return () => {
      marker.remove();
      markerRef.current = null;
    };
  }, [map, longitude, latitude, label]);

  return null;
}
