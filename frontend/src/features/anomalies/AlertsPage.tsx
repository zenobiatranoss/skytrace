import { useNavigate } from "react-router-dom";

import { useAnomalies } from "../../hooks/useAnomalies";
import { mapSelection } from "../../hooks/useMapSelection";
import type { Anomaly } from "../../types/anomaly";
import {
  countBySeverity,
  SEVERITY_ORDER,
  severityColor,
  severityLabel,
} from "../../utils/anomaly";
import { AnomalyList } from "./AnomalyList";

export function AlertsPage() {
  const anomalies = useAnomalies();
  const navigate = useNavigate();
  const counts = countBySeverity(anomalies);

  function open(anomaly: Anomaly) {
    mapSelection.selectAircraft(anomaly.icao24);
    if (anomaly.latitude !== null && anomaly.longitude !== null) {
      mapSelection.focusOn(anomaly.longitude, anomaly.latitude, 7);
    }
    navigate("/");
  }

  return (
    <div className="page">
      <div className="page-inner">
        <h2>Alerts</h2>
        <p style={{ color: "var(--muted)", fontSize: 13 }}>
          Behaviours flagged by the detectors. These are signals worth a look,
          not confirmed events, and they clear on their own once the condition
          stops.
        </p>

        <div className="severity-summary">
          {SEVERITY_ORDER.filter((severity) => counts[severity]).map(
            (severity) => (
              <span
                key={severity}
                className="sev-chip"
                style={{
                  borderColor: severityColor(severity),
                  color: severityColor(severity),
                }}
              >
                {counts[severity]} {severityLabel(severity)}
              </span>
            ),
          )}
        </div>

        <AnomalyList anomalies={anomalies} onSelect={open} />
      </div>
    </div>
  );
}
