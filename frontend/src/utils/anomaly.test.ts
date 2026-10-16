import { describe, expect, it } from "vitest";

import {
  countBySeverity,
  kindLabel,
  severityByAircraft,
  severityColor,
  severityRank,
} from "./anomaly";
import type { Anomaly } from "../types/anomaly";

function anomaly(overrides: Partial<Anomaly>): Anomaly {
  return {
    id: 1,
    icao24: "abc123",
    callsign: "TEST1",
    kind: "low_speed",
    severity: "low",
    message: "low airspeed",
    latitude: 1,
    longitude: 2,
    first_seen: "2026-01-01T00:00:00Z",
    last_seen: "2026-01-01T00:00:00Z",
    active: true,
    ...overrides,
  };
}

describe("severityByAircraft", () => {
  it("keeps the worst severity per aircraft", () => {
    const map = severityByAircraft([
      anomaly({ icao24: "a", severity: "low" }),
      anomaly({ icao24: "a", severity: "critical" }),
      anomaly({ icao24: "b", severity: "medium" }),
    ]);

    expect(map.get("a")).toBe("critical");
    expect(map.get("b")).toBe("medium");
  });

  it("is empty with no anomalies", () => {
    expect(severityByAircraft([]).size).toBe(0);
  });
});

describe("countBySeverity", () => {
  it("counts anomalies per severity", () => {
    const counts = countBySeverity([
      anomaly({ severity: "high" }),
      anomaly({ severity: "high" }),
      anomaly({ severity: "low" }),
    ]);

    expect(counts.high).toBe(2);
    expect(counts.low).toBe(1);
    expect(counts.critical).toBeUndefined();
  });
});

describe("severity helpers", () => {
  it("ranks severities so critical beats the rest", () => {
    expect(severityRank("critical")).toBeGreaterThan(severityRank("high"));
    expect(severityRank("high")).toBeGreaterThan(severityRank("medium"));
    expect(severityRank("medium")).toBeGreaterThan(severityRank("low"));
    expect(severityRank("nonsense")).toBe(0);
  });

  it("falls back to a neutral colour for unknown severities", () => {
    expect(severityColor("critical")).toBe("#f87171");
    expect(severityColor("nonsense")).toBe("#94a3b8");
  });

  it("labels known kinds and echoes unknown ones", () => {
    expect(kindLabel("position_jump")).toBe("Position jump");
    expect(kindLabel("something_new")).toBe("something_new");
  });
});
