export interface Airport {
  id: number;
  icao: string | null;
  iata: string | null;
  name: string;
  city: string | null;
  country: string | null;
  latitude: number;
  longitude: number;
  elevation_ft: number | null;
}
