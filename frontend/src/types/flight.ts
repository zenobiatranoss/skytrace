export interface TrackPoint {
  latitude: number;
  longitude: number;
  altitude_m: number | null;
  velocity_ms: number | null;
  heading: number | null;
  recorded_at: string;
}

export interface Track {
  icao24: string;
  callsign: string | null;
  observed: boolean;
  points: TrackPoint[];
}

export interface FlightSummary {
  flight_id: number | null;
  callsign: string | null;
  icao24: string;
  departure_icao: string | null;
  arrival_icao: string | null;
  status: string;
  scheduled_time: string | null;
  last_seen: string | null;
}

export interface FlightDetail extends FlightSummary {
  id: number;
  first_seen: string;
  last_latitude: number | null;
  last_longitude: number | null;
  last_altitude: number | null;
  last_velocity: number | null;
  track: TrackPoint[];
}
