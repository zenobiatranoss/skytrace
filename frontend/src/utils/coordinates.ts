export const METERS_PER_FOOT = 0.3048;
export const MS_PER_KNOT = 0.514444;
export const MS_PER_FPM = 0.00508;

export function metersToFeet(meters: number | null): number | null {
  if (meters === null) return null;
  return meters / METERS_PER_FOOT;
}

export function msToKnots(ms: number | null): number | null {
  if (ms === null) return null;
  return ms / MS_PER_KNOT;
}

export function msToFeetPerMinute(ms: number | null): number | null {
  if (ms === null) return null;
  return ms / MS_PER_FPM;
}

export function normalizeHeading(deg: number | null): number | null {
  if (deg === null) return null;
  return ((deg % 360) + 360) % 360;
}

const EARTH_RADIUS_KM = 6371;

export function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
}
