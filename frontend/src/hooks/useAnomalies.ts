import { useEffect, useState } from "react";

import { useFlightUpdates } from "./useFlightUpdates";
import { fetchAnomalies } from "../services/anomalyApi";
import type { Anomaly } from "../types/anomaly";

// anomalies ride along on the live feed, but we also poll the rest endpoint:
// it populates the view on first load instead of waiting for the next
// broadcast, and it keeps the last known set visible if the feed hiccups.
export function useAnomalies(pollMs = 20000): Anomaly[] {
  const live = useFlightUpdates();
  const [rest, setRest] = useState<Anomaly[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetchAnomalies({ limit: 500 });
        if (!cancelled) setRest(response.items);
      } catch {
        // keep whatever we had
      }
    }

    load();
    const timer = window.setInterval(load, pollMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [pollMs]);

  // prefer the fresher live set once it carries something
  return live.anomalies.length > 0 ? live.anomalies : rest;
}
