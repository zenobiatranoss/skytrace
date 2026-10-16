import { useCallback, useEffect, useState } from "react";

import { fetchFlights } from "../services/flightApi";
import type { FlightSummary } from "../types/flight";

interface UseFlightsResult {
  flights: FlightSummary[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFlights(pollMs = 30000): UseFlightsResult {
  const [flights, setFlights] = useState<FlightSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setFlights(await fetchFlights());
      setError(null);
    } catch {
      setError("failed to load flights");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, pollMs);
    return () => window.clearInterval(timer);
  }, [load, pollMs]);

  return { flights, loading, error, refetch: load };
}
