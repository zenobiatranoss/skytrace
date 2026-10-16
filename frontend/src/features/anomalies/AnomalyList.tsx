import type { Anomaly } from "../../types/anomaly";
import { kindLabel, severityColor } from "../../utils/anomaly";

interface Props {
  anomalies: Anomaly[];
  onSelect?: (anomaly: Anomaly) => void;
}

export function AnomalyList({ anomalies, onSelect }: Props) {
  if (anomalies.length === 0) {
    return <p className="empty-note">No active alerts.</p>;
  }

  return (
    <ul className="anomaly-list">
      {anomalies.map((anomaly, index) => (
        <li
          key={`${anomaly.icao24}-${anomaly.kind}-${index}`}
          onClick={() => onSelect?.(anomaly)}
          style={{ cursor: onSelect ? "pointer" : "default" }}
        >
          <span
            className="severity-dot"
            style={{ background: severityColor(anomaly.severity) }}
          />
          <div className="anomaly-main">
            <div className="anomaly-title">
              {anomaly.callsign || anomaly.icao24}
            </div>
            <div className="anomaly-message">{anomaly.message}</div>
          </div>
          <span
            className="anomaly-kind"
            style={{ color: severityColor(anomaly.severity) }}
          >
            {kindLabel(anomaly.kind)}
          </span>
        </li>
      ))}
    </ul>
  );
}
