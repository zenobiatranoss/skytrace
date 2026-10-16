import { useEffect, useState } from "react";

import { useAnomalies } from "../../hooks/useAnomalies";
import { fetchAircraftAnomalies } from "../../services/anomalyApi";
import type { Anomaly } from "../../types/anomaly";
import { AnomalyList } from "./AnomalyList";

export function AircraftAnomalies({ icao24 }: { icao24: string }) {
  const live = useAnomalies();
  const liveForAircraft = live.filter((item) => item.icao24 === icao24);

  const [rest, setRest] = useState<Anomaly[]>([]);
  useEffect(() => {
    let cancelled = false;
    fetchAircraftAnomalies(icao24)
      .then((items) => {
        if (!cancelled) setRest(items.filter((item) => item.active));
      })
      .catch(() => {
        if (!cancelled) setRest([]);
      });
    return () => {
      cancelled = true;
    };
  }, [icao24]);

  const items = liveForAircraft.length > 0 ? liveForAircraft : rest;
  return <AnomalyList anomalies={items} />;
}
