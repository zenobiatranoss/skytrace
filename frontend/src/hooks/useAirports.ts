import { useCallback, useEffect, useState } from "react";

import {
  fetchAirport,
  fetchArrivals,
  fetchDepartures,
} from "../services/airportApi";
import type { Airport } from "../types/airport";
import type { FlightSummary } from "../types/flight";

interface UseAirportResult {
  airport: Airport | null;
  arrivals: FlightSummary[];
  departures: FlightSummary[];
  loading: boolean;
  error: string | null;
}

export function useAirports(code: string | null): UseAirportResult {
  const [state, setState] = useState<UseAirportResult>({
    airport: null,
    arrivals: [],
    departures: [],
    loading: false,
    error: null,
  });

  const load = useCallback(async (target: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const [airport, arrivals, departures] = await Promise.all([
        fetchAirport(target),
        fetchArrivals(target).catch(() => []),
        fetchDepartures(target).catch(() => []),
      ]);
      setState({ airport, arrivals, departures, loading: false, error: null });
    } catch {
      setState({
        airport: null,
        arrivals: [],
        departures: [],
        loading: false,
        error: `could not load airport ${target}`,
      });
    }
  }, []);

  useEffect(() => {
    if (code) load(code);
  }, [code, load]);

  return state;
}
