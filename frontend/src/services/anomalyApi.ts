import type { Anomaly, AnomalyResponse } from "../types/anomaly";
import { buildQuery, request } from "./api";

export function fetchAnomalies(
  params: { severity?: string; kind?: string; limit?: number } = {},
): Promise<AnomalyResponse> {
  return request(`/anomalies${buildQuery(params)}`);
}

export function fetchAircraftAnomalies(icao24: string): Promise<Anomaly[]> {
  return request(`/anomalies/${icao24}`);
}
