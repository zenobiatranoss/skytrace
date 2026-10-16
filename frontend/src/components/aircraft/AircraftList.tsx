import type { AircraftPosition } from "../../types/aircraft";
import { statusColor, statusLabel } from "../../utils/flightStatus";
import { formatAltitude, formatSpeed } from "../../utils/formatters";
import { EmptyState } from "../common/EmptyState";

interface Props {
  aircraft: AircraftPosition[];
  onSelect: (icao24: string) => void;
  limit?: number;
}

export function AircraftList({ aircraft, onSelect, limit = 100 }: Props) {
  if (aircraft.length === 0) {
    return <EmptyState message="No aircraft to show." />;
  }

  return (
    <div>
      {aircraft.slice(0, limit).map((plane) => (
        <div
          key={plane.icao24}
          className="list-row"
          onClick={() => onSelect(plane.icao24)}
        >
          <span
            className="status-dot"
            style={{ background: statusColor(plane.status) }}
          />
          <strong>{plane.callsign || plane.icao24}</strong>
          <span style={{ color: "var(--muted)", fontSize: 12 }}>
            {plane.registration || statusLabel(plane.status)}
          </span>
          <span style={{ marginLeft: "auto", fontSize: 12 }}>
            {formatAltitude(plane.altitude_m)} · {formatSpeed(plane.velocity_ms)}
          </span>
        </div>
      ))}
    </div>
  );
}
