import type { Anomaly } from "../types/anomaly";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#f87171",
  high: "#fb923c",
  medium: "#facc15",
  low: "#94a3b8",
};

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

const SEVERITY_RANK: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

const KIND_LABELS: Record<string, string> = {
  emergency_squawk: "Emergency squawk",
  rapid_descent: "Rapid descent",
  rapid_climb: "Rapid climb",
  low_speed: "Low airspeed",
  position_jump: "Position jump",
  loitering: "Loitering",
};

export const SEVERITY_ORDER = ["critical", "high", "medium", "low"];

export function severityColor(severity: string): string {
  return SEVERITY_COLORS[severity] ?? SEVERITY_COLORS.low;
}

export function severityLabel(severity: string): string {
  return SEVERITY_LABELS[severity] ?? "Low";
}

export function kindLabel(kind: string): string {
  return KIND_LABELS[kind] ?? kind;
}

export function severityRank(severity: string): number {
  return SEVERITY_RANK[severity] ?? 0;
}

// one entry per aircraft, keeping the worst severity it carries - the map
// only needs to know how loudly to shout.
export function severityByAircraft(anomalies: Anomaly[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const anomaly of anomalies) {
    const current = map.get(anomaly.icao24);
    if (current === undefined || severityRank(anomaly.severity) > severityRank(current)) {
      map.set(anomaly.icao24, anomaly.severity);
    }
  }
  return map;
}

export function countBySeverity(anomalies: Anomaly[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const anomaly of anomalies) {
    counts[anomaly.severity] = (counts[anomaly.severity] ?? 0) + 1;
  }
  return counts;
}
