import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Anomaly } from "../../types/anomaly";

const navigate = vi.fn();
vi.mock("react-router-dom", () => ({ useNavigate: () => navigate }));
vi.mock("../../hooks/useAnomalies", () => ({ useAnomalies: vi.fn() }));

import { AlertsPage } from "./AlertsPage";
import { useAnomalies } from "../../hooks/useAnomalies";
import { mapSelection } from "../../hooks/useMapSelection";

function anomaly(overrides: Partial<Anomaly>): Anomaly {
  return {
    id: 1,
    icao24: "abc123",
    callsign: "TEST1",
    kind: "low_speed",
    severity: "medium",
    message: "Low airspeed (50 kt)",
    latitude: 40.46,
    longitude: 1.92,
    first_seen: "2026-01-01T00:00:00Z",
    last_seen: "2026-01-01T00:00:00Z",
    active: true,
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AlertsPage", () => {
  it("shows a chip per severity present and lists the anomalies", () => {
    vi.mocked(useAnomalies).mockReturnValue([
      anomaly({ callsign: "EZY123", kind: "emergency_squawk", severity: "critical" }),
      anomaly({ icao24: "def456", callsign: "N42", kind: "loitering", severity: "medium" }),
    ]);

    render(<AlertsPage />);

    expect(screen.getByText("1 Critical")).toBeInTheDocument();
    expect(screen.getByText("1 Medium")).toBeInTheDocument();
    expect(screen.getByText("EZY123")).toBeInTheDocument();
    expect(screen.getByText("N42")).toBeInTheDocument();
  });

  it("selects the aircraft and returns to the map when a row is clicked", () => {
    const select = vi.spyOn(mapSelection, "selectAircraft");
    const focus = vi.spyOn(mapSelection, "focusOn");
    vi.mocked(useAnomalies).mockReturnValue([anomaly({ callsign: "EZY123" })]);

    render(<AlertsPage />);
    fireEvent.click(screen.getByText("EZY123"));

    expect(select).toHaveBeenCalledWith("abc123");
    expect(focus).toHaveBeenCalledWith(1.92, 40.46, 7);
    expect(navigate).toHaveBeenCalledWith("/");
  });

  it("copes with no alerts", () => {
    vi.mocked(useAnomalies).mockReturnValue([]);
    render(<AlertsPage />);
    expect(screen.getByText("No active alerts.")).toBeInTheDocument();
  });
});
