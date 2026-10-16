export type AnomalySeverity = "critical" | "high" | "medium" | "low";

export interface Anomaly {
  id: number | null;
  icao24: string;
  callsign: string | null;
  kind: string;
  severity: string;
  message: string;
  latitude: number | null;
  longitude: number | null;
  first_seen: string;
  last_seen: string;
  active: boolean;
}

export interface AnomalyResponse {
  count: number;
  items: Anomaly[];
}
