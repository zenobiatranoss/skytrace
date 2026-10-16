import type { AircraftDetail, AircraftPosition } from "../types/aircraft";
import type { Bounds, SearchResponse } from "../types/api";
import { buildQuery, request } from "./api";

export function fetchAircraft(
  bounds?: Bounds | null,
  limit?: number,
): Promise<AircraftPosition[]> {
  return request(`/aircraft${buildQuery({ ...(bounds ?? {}), limit })}`);
}

export function fetchAircraftDetail(icao24: string): Promise<AircraftDetail> {
  return request(`/aircraft/${icao24}`);
}

export function searchAircraft(query: string): Promise<SearchResponse> {
  return request(`/search${buildQuery({ q: query })}`);
}
