import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AnomalyList } from "./AnomalyList";
import type { Anomaly } from "../../types/anomaly";

function anomaly(overrides: Partial<Anomaly>): Anomaly {
  return {
    id: 1,
    icao24: "abc123",
    callsign: "TEST1",
    kind: "low_speed",
    severity: "low",
    message: "Low airspeed at high altitude",
    latitude: 40.46,
    longitude: 1.92,
    first_seen: "2026-01-01T00:00:00Z",
    last_seen: "2026-01-01T00:00:00Z",
    active: true,
    ...overrides,
  };
}

describe("AnomalyList", () => {
  it("shows an empty note when there is nothing to flag", () => {
    render(<AnomalyList anomalies={[]} />);
    expect(screen.getByText("No active alerts.")).toBeInTheDocument();
  });

  it("renders each anomaly with its call sign and message", () => {
    render(
      <AnomalyList
        anomalies={[
          anomaly({}),
          anomaly({
            icao24: "def456",
            callsign: "TEST2",
            kind: "position_jump",
            severity: "critical",
            message: "Impossible position change",
          }),
        ]}
      />,
    );

    expect(screen.getByText("TEST1")).toBeInTheDocument();
    expect(screen.getByText("TEST2")).toBeInTheDocument();
    expect(screen.getByText("Low airspeed at high altitude")).toBeInTheDocument();
    expect(screen.getByText("Position jump")).toBeInTheDocument();
  });

  it("uses the icao24 when there is no call sign", () => {
    render(<AnomalyList anomalies={[anomaly({ callsign: null })]} />);
    expect(screen.getByText("abc123")).toBeInTheDocument();
  });

  it("reports the clicked anomaly", () => {
    const onSelect = vi.fn();
    const target = anomaly({ callsign: "TEST9" });
    render(<AnomalyList anomalies={[target]} onSelect={onSelect} />);

    fireEvent.click(screen.getByText("TEST9"));
    expect(onSelect).toHaveBeenCalledWith(target);
  });
});
