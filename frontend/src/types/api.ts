export interface ApiError {
  detail: string;
}

export interface Bounds {
  lamin: number;
  lomin: number;
  lamax: number;
  lomax: number;
}

export type SearchKind = "aircraft" | "airport" | "flight";

export interface SearchResult {
  kind: SearchKind;
  id: string;
  label: string;
  subtitle: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}
