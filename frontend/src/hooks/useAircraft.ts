import { useCallback, useEffect, useRef, useState } from "react";

import { fetchAircraft } from "../services/aircraftApi";
import type { AircraftPosition } from "../types/aircraft";
import { ApiRequestError } from "../services/api";

interface UseAircraftResult {
  aircraft: AircraftPosition[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

// rest fallback for when the websocket isn't available. polls slowly -
// the live feed is the primary path.
export function useAircraft(pollMs = 15000): UseAircraftResult {
  const [aircraft, setAircraft] = useState<AircraftPosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);

  const load = useCallback(async () => {
    try {
      const data = await fetchAircraft();
      if (!mounted.current) return;
      setAircraft(data);
      setError(null);
    } catch (err) {
      if (!mounted.current) return;
      setError(
        err instanceof ApiRequestError ? err.message : "failed to load aircraft",
      );
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    load();
    const timer = window.setInterval(load, pollMs);
    return () => {
      mounted.current = false;
      window.clearInterval(timer);
    };
  }, [load, pollMs]);

  return { aircraft, loading, error, refetch: load };
}
