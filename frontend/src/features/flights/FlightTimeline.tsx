import type { TrackPoint } from "../../types/flight";
import { formatTime } from "../../utils/formatters";

const MAX_ROWS = 6;

export function FlightTimeline({ points }: { points: TrackPoint[] }) {
  if (points.length === 0) {
    return <p className="empty-note">No recorded positions for this flight.</p>;
  }

  // newest first reads better in a narrow panel
  const recent = [...points].reverse().slice(0, MAX_ROWS);

  return (
    <ul className="timeline">
      {recent.map((point, index) => (
        <li key={`${point.recorded_at}-${index}`}>
          <span className="time">{formatTime(point.recorded_at)}</span>
          <span className="coords">
            {point.latitude.toFixed(3)}, {point.longitude.toFixed(3)}
          </span>
        </li>
      ))}
    </ul>
  );
}
