import type { AircraftStatus } from "../types/aircraft";

export const STATUS_LABELS: Record<AircraftStatus, string> = {
  airborne: "Airborne",
  on_ground: "On ground",
  stale: "Stale",
  unknown: "Unknown",
};

export const STATUS_COLORS: Record<AircraftStatus, string> = {
  airborne: "#4ade80",
  on_ground: "#facc15",
  stale: "#94a3b8",
  unknown: "#64748b",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status as AircraftStatus] ?? "Unknown";
}

export function statusColor(status: string): string {
  return STATUS_COLORS[status as AircraftStatus] ?? STATUS_COLORS.unknown;
}
