import type { Track } from "../../types/flight";
import { haversineKm } from "../../utils/coordinates";
import { formatTime } from "../../utils/formatters";

export function FlightHistory({ track }: { track: Track | null }) {
  const points = track?.points ?? [];

  if (points.length < 2) {
    return (
      <p className="empty-note">
        {track
          ? "Not enough observed positions to draw a path yet."
          : "Loading observed path…"}
      </p>
    );
  }

  let distance = 0;
  for (let i = 1; i < points.length; i += 1) {
    distance += haversineKm(
      points[i - 1].latitude,
      points[i - 1].longitude,
      points[i].latitude,
      points[i].longitude,
    );
  }

  return (
    <div className="field-grid">
      <div className="field">
        <span className="label">Observed points</span>
        <span className="value">{points.length}</span>
      </div>
      <div className="field">
        <span className="label">Path length</span>
        <span className="value">{Math.round(distance)} km</span>
      </div>
      <div className="field">
        <span className="label">First seen</span>
        <span className="value">{formatTime(points[0].recorded_at)}</span>
      </div>
      <div className="field">
        <span className="label">Last seen</span>
        <span className="value">
          {formatTime(points[points.length - 1].recorded_at)}
        </span>
      </div>
    </div>
  );
}
