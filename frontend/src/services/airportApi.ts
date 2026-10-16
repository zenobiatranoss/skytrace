import type { Airport } from "../types/airport";
import type { FlightSummary } from "../types/flight";
import { request } from "./api";

export function fetchAirport(code: string): Promise<Airport> {
  return request(`/airports/${encodeURIComponent(code)}`);
}

export function fetchArrivals(code: string): Promise<FlightSummary[]> {
  return request(`/airports/${encodeURIComponent(code)}/arrivals`);
}

export function fetchDepartures(code: string): Promise<FlightSummary[]> {
  return request(`/airports/${encodeURIComponent(code)}/departures`);
}
