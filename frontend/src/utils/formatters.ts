import {
  metersToFeet,
  msToFeetPerMinute,
  msToKnots,
} from "./coordinates";

const numberFormat = new Intl.NumberFormat("en-US");

const UNAVAILABLE = "—";

export function formatAltitude(meters: number | null): string {
  const feet = metersToFeet(meters);
  if (feet === null) return UNAVAILABLE;
  return `${numberFormat.format(Math.round(feet))} ft`;
}

export function formatSpeed(ms: number | null): string {
  const knots = msToKnots(ms);
  if (knots === null) return UNAVAILABLE;
  return `${numberFormat.format(Math.round(knots))} kt`;
}

export function formatVerticalRate(ms: number | null): string {
  const fpm = msToFeetPerMinute(ms);
  if (fpm === null) return UNAVAILABLE;
  const rounded = Math.round(fpm);
  const sign = rounded > 0 ? "+" : "";
  return `${sign}${numberFormat.format(rounded)} ft/min`;
}

export function formatHeading(deg: number | null): string {
  if (deg === null) return UNAVAILABLE;
  return `${Math.round(deg)}°`;
}

export function formatCoords(
  lat: number | null,
  lon: number | null,
  digits = 4,
): string {
  if (lat === null || lon === null) return UNAVAILABLE;
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(digits)}°${ns}, ${Math.abs(lon).toFixed(digits)}°${ew}`;
}

export function formatAge(seconds: number | null): string {
  if (seconds === null) return UNAVAILABLE;
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export function formatTime(iso: string | null): string {
  if (!iso) return UNAVAILABLE;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return UNAVAILABLE;
  return date.toLocaleTimeString();
}

export function orUnavailable(value: string | null | undefined): string {
  return value && value.trim() ? value : UNAVAILABLE;
}

export { UNAVAILABLE };
