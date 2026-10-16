import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { useFlightUpdates } from "../../hooks/useFlightUpdates";
import { useAircraft } from "../../hooks/useAircraft";
import { useAnomalies } from "../../hooks/useAnomalies";
import { mapSelection, useMapSelection } from "../../hooks/useMapSelection";
import { fetchTrack } from "../../services/flightApi";
import type { AircraftPosition } from "../../types/aircraft";
import type { Track } from "../../types/flight";
import { statusColor } from "../../utils/flightStatus";
import { severityByAircraft } from "../../utils/anomaly";
import { FlightPath } from "./FlightPath";
import { AircraftMarker, loadPlaneImage } from "./AircraftMarker";
import { AirportMarker } from "./AirportMarker";
import { MapControls } from "./MapControls";
import {
  AircraftFilters,
  applyFilters,
  defaultFilters,
  type AircraftFilterState,
} from "../aircraft/AircraftFilters";

const STYLE_URL =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const HOME_CENTER: [number, number] = [0, 0];
const HOME_ZOOM = 1.5;

const PLANE_IMAGES: Array<[string, string]> = [
  ["plane-air", "#4ade80"],
  ["plane-ground", "#facc15"],
  ["plane-stale", "#94a3b8"],
  ["plane-unknown", "#64748b"],
];

const EMPTY: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [],
};

function toFeatureCollection(
  aircraft: AircraftPosition[],
  severity: Map<string, string>,
): GeoJSON.FeatureCollection {
  const features: GeoJSON.Feature[] = [];

  for (const plane of aircraft) {
    if (plane.latitude === null || plane.longitude === null) continue;
    const properties: GeoJSON.Feature["properties"] = {
      icao24: plane.icao24,
      callsign: plane.callsign,
      heading: plane.heading ?? 0,
      status: plane.status,
    };
    const planeSeverity = severity.get(plane.icao24);
    if (planeSeverity) properties.severity = planeSeverity;
    features.push({
      type: "Feature",
      geometry: { type: "Point", coordinates: [plane.longitude, plane.latitude] },
      properties,
    });
  }

  return { type: "FeatureCollection", features };
}

export function FlightMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<maplibregl.Map | null>(null);

  const live = useFlightUpdates();
  const rest = useAircraft();
  // prefer the live feed, but fall back to rest polling if it's down
  const aircraft = live.aircraft.length > 0 ? live.aircraft : rest.aircraft;

  const anomalies = useAnomalies();
  const severity = useMemo(() => severityByAircraft(anomalies), [anomalies]);

  const [filters, setFilters] = useState<AircraftFilterState>(defaultFilters);
  const [following, setFollowing] = useState(false);
  const [track, setTrack] = useState<Track | null>(null);

  const { selection, focus } = useMapSelection();

  const visible = useMemo(
    () => applyFilters(aircraft, filters),
    [aircraft, filters],
  );

  const selectedAircraft =
    selection?.type === "aircraft"
      ? aircraft.find((plane) => plane.icao24 === selection.id) ?? null
      : null;

  // set the map up once
  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;

    const instance = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: HOME_CENTER,
      zoom: HOME_ZOOM,
      attributionControl: { compact: true },
    });

    instance.on("load", () => {
      if (!cancelled) setMap(instance);
    });
    return () => {
      cancelled = true;
      instance.remove();
      setMap(null);
    };
  }, []);

  // sources, layers, images and interaction
  useEffect(() => {
    if (!map) return;
    let cancelled = false;

    async function setup() {
      await Promise.all(
        PLANE_IMAGES.map(async ([name, color]) => {
          const image = await loadPlaneImage(color, 48);
          if (!cancelled) map!.addImage(name, image, { pixelRatio: 2 });
        }),
      );
      if (cancelled) return;

      map!.addSource("aircraft", { type: "geojson", data: EMPTY });

      // halo behind flagged aircraft, drawn first so the plane sits on top
      map!.addLayer({
        id: "aircraft-alerts",
        type: "circle",
        source: "aircraft",
        filter: ["has", "severity"],
        paint: {
          "circle-color": [
            "match",
            ["get", "severity"],
            "critical",
            "#f87171",
            "high",
            "#fb923c",
            "medium",
            "#facc15",
            "low",
            "#94a3b8",
            "#94a3b8",
          ],
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0,
            4,
            6,
            9,
            12,
            16,
          ],
          "circle-opacity": 0.25,
          "circle-stroke-color": [
            "match",
            ["get", "severity"],
            "critical",
            "#f87171",
            "high",
            "#fb923c",
            "medium",
            "#facc15",
            "low",
            "#94a3b8",
            "#94a3b8",
          ],
          "circle-stroke-width": 1.5,
          "circle-stroke-opacity": 0.9,
        },
      });

      map!.addLayer({
        id: "aircraft-symbols",
        type: "symbol",
        source: "aircraft",
        layout: {
          "icon-image": [
            "match",
            ["get", "status"],
            "on_ground",
            "plane-ground",
            "stale",
            "plane-stale",
            "unknown",
            "plane-unknown",
            "plane-air",
          ],
          "icon-rotate": ["get", "heading"],
          "icon-rotation-alignment": "map",
          "icon-allow-overlap": true,
          "icon-ignore-placement": true,
          "icon-size": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0,
            0.35,
            6,
            0.6,
            12,
            1,
          ],
        },
      });

      map!.addLayer({
        id: "aircraft-labels",
        type: "symbol",
        source: "aircraft",
        minzoom: 6,
        layout: {
          "text-field": ["get", "callsign"],
          "text-size": 11,
          "text-offset": [0, 1.3],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#cbd5e1",
          "text-halo-color": "#0b0f14",
          "text-halo-width": 1.2,
        },
      });

      map!.on("click", "aircraft-symbols", (event) => {
        const feature = event.features?.[0];
        const icao24 = feature?.properties?.icao24 as string | undefined;
        if (icao24) mapSelection.selectAircraft(icao24);
      });

      map!.on("click", "aircraft-alerts", (event) => {
        const feature = event.features?.[0];
        const icao24 = feature?.properties?.icao24 as string | undefined;
        if (icao24) mapSelection.selectAircraft(icao24);
      });

      map!.on("click", (event) => {
        const hits = map!.queryRenderedFeatures(event.point, {
          layers: ["aircraft-symbols", "aircraft-alerts"],
        });
        // clicked open water - drop the selection
        if (hits.length === 0) mapSelection.clear();
      });

      map!.on("mouseenter", "aircraft-symbols", () => {
        map!.getCanvas().style.cursor = "pointer";
      });
      map!.on("mouseleave", "aircraft-symbols", () => {
        map!.getCanvas().style.cursor = "";
      });
      map!.on("mouseenter", "aircraft-alerts", () => {
        map!.getCanvas().style.cursor = "pointer";
      });
      map!.on("mouseleave", "aircraft-alerts", () => {
        map!.getCanvas().style.cursor = "";
      });
    }

    setup();
    return () => {
      cancelled = true;
      // the map may already be torn down; ignore whatever's gone
      try {
        if (map.getLayer("aircraft-labels")) map.removeLayer("aircraft-labels");
        if (map.getLayer("aircraft-symbols")) map.removeLayer("aircraft-symbols");
        if (map.getLayer("aircraft-alerts")) map.removeLayer("aircraft-alerts");
        if (map.getSource("aircraft")) map.removeSource("aircraft");
        for (const [name] of PLANE_IMAGES) {
          if (map.hasImage(name)) map.removeImage(name);
        }
      } catch {
        // map already removed, nothing to clean up
      }
    };
  }, [map]);

  // keep the aircraft source in sync with the visible set
  useEffect(() => {
    if (!map) return;
    const source = map.getSource("aircraft") as maplibregl.GeoJSONSource | undefined;
    source?.setData(toFeatureCollection(visible, severity));
  }, [map, visible, severity]);

  // fly to whatever was requested
  useEffect(() => {
    if (!map || !focus) return;
    map.flyTo({
      center: [focus.longitude, focus.latitude],
      zoom: focus.zoom ?? Math.max(map.getZoom(), 6),
      duration: 900,
    });
  }, [map, focus]);

  // pull the observed path for the selected aircraft
  useEffect(() => {
    if (selection?.type !== "aircraft") {
      setTrack(null);
      return;
    }

    let cancelled = false;
    fetchTrack(selection.id)
      .then((data) => {
        if (!cancelled) setTrack(data);
      })
      .catch(() => {
        if (!cancelled) setTrack(null);
      });

    return () => {
      cancelled = true;
    };
  }, [selection]);

  // recenter on the selected aircraft while following
  useEffect(() => {
    if (!map || !following || !selectedAircraft) return;
    if (selectedAircraft.longitude === null || selectedAircraft.latitude === null) {
      return;
    }
    map.easeTo({
      center: [selectedAircraft.longitude, selectedAircraft.latitude],
      duration: 600,
    });
  }, [map, following, selectedAircraft]);

  return (
    <div className="map-container" ref={containerRef}>
      {map && <AircraftFilters filters={filters} onChange={setFilters} />}

      {map && (
        <MapControls
          map={map}
          following={following}
          onToggleFollow={() => setFollowing((value) => !value)}
        />
      )}

      {map && selectedAircraft && selectedAircraft.longitude !== null &&
        selectedAircraft.latitude !== null && (
          <AircraftMarker
            map={map}
            longitude={selectedAircraft.longitude}
            latitude={selectedAircraft.latitude}
            heading={selectedAircraft.heading}
            color={statusColor(selectedAircraft.status)}
          />
        )}

      {map && selection?.type === "airport" && focus && (
        <AirportMarker
          map={map}
          longitude={focus.longitude}
          latitude={focus.latitude}
          label={selection.id}
        />
      )}

      {map && selection?.type === "aircraft" && (
        <FlightPath map={map} track={track} />
      )}

      {!selection && (
        <div className="panel-hint">
          Click an aircraft on the map to see its details
        </div>
      )}
    </div>
  );
}
