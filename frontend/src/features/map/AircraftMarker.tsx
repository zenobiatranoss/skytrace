import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

// material "flight" glyph, nose pointing up (north) so heading maps directly
// onto icon rotation
const PLANE_PATH =
  "M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 " +
  "3.5 1v-1.5L13 19v-5.5l8 2.5z";

export function planeSvg(color: string, size = 24): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24"><path fill="${color}" d="${PLANE_PATH}"/></svg>`;
}

export function planeDataUrl(color: string, size = 24): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(planeSvg(color, size))}`;
}

export function loadPlaneImage(color: string, size = 48): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = planeDataUrl(color, size);
  });
}

interface Props {
  map: maplibregl.Map;
  longitude: number;
  latitude: number;
  heading: number | null;
  color: string;
}

// a single highlighted plane for the selected aircraft, drawn as a dom
// marker on top of the symbol layer so it stands out
export function AircraftMarker({ map, longitude, latitude, heading, color }: Props) {
  const markerRef = useRef<maplibregl.Marker | null>(null);

  useEffect(() => {
    const element = document.createElement("div");
    element.className = "selected-marker";
    element.style.width = "30px";
    element.style.height = "30px";
    element.style.backgroundImage = `url("${planeDataUrl(color, 30)}")`;
    element.style.backgroundSize = "contain";
    element.style.backgroundRepeat = "no-repeat";

    const marker = new maplibregl.Marker({
      element,
      rotationAlignment: "map",
    })
      .setLngLat([longitude, latitude])
      .addTo(map);

    markerRef.current = marker;
    return () => {
      marker.remove();
      markerRef.current = null;
    };
  }, [map, color]);

  useEffect(() => {
    markerRef.current?.setLngLat([longitude, latitude]);
    markerRef.current?.setRotation(heading ?? 0);
  }, [longitude, latitude, heading]);

  return null;
}
