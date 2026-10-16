import type { FlightDetail, FlightSummary, Track } from "../types/flight";
import { buildQuery, request } from "./api";

export function fetchFlights(limit = 100): Promise<FlightSummary[]> {
  return request(`/flights${buildQuery({ limit })}`);
}

export function fetchFlightDetail(id: number): Promise<FlightDetail> {
  return request(`/flights/${id}`);
}

export function fetchTrack(icao24: string, hours = 6): Promise<Track> {
  return request(`/aircraft/${icao24}/track${buildQuery({ hours })}`);
}
