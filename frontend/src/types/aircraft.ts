export type AircraftStatus = "unknown" | "on_ground" | "airborne" | "stale";

// flat shape the map and list work with
export interface AircraftPosition {
  icao24: string;
  callsign: string | null;
  registration: string | null;
  type_code: string | null;
  latitude: number | null;
  longitude: number | null;
  altitude_m: number | null;
  velocity_ms: number | null;
  heading: number | null;
  vertical_rate_ms: number | null;
  on_ground: boolean | null;
  status: AircraftStatus;
  last_contact: string | null;
  age_seconds: number | null;
  is_stale: boolean;
}

export interface AircraftIdentity {
  icao24: string;
  registration: string | null;
  callsign: string | null;
  type_code: string | null;
  model: string | null;
  operator: string | null;
  country: string | null;
}

export interface StateVector {
  icao24: string;
  callsign: string | null;
  origin_country: string | null;
  latitude: number | null;
  longitude: number | null;
  altitude_m: number | null;
  geo_altitude_m: number | null;
  velocity_ms: number | null;
  heading: number | null;
  vertical_rate_ms: number | null;
  on_ground: boolean | null;
  squawk: string | null;
  position_source: number | null;
  time_position: string | null;
  last_contact: string | null;
}

export interface AircraftDetail {
  identity: AircraftIdentity;
  position: StateVector | null;
  status: AircraftStatus;
  age_seconds: number | null;
  is_stale: boolean;
  departure_icao: string | null;
  arrival_icao: string | null;
  departure_name: string | null;
  arrival_name: string | null;
  departure_iata: string | null;
  arrival_iata: string | null;
  airline: string | null;
  photo_url: string | null;
  photo_thumbnail: string | null;
}
