import { useAnomalies } from "../../hooks/useAnomalies";
import { useFlightUpdates } from "../../hooks/useFlightUpdates";
import { formatAge } from "../../utils/formatters";

export function StatusBar() {
  const { aircraft, updatedAt, error } = useFlightUpdates();
  const anomalies = useAnomalies();

  const lastUpdate = updatedAt ? new Date(updatedAt) : null;
  const ageSeconds = lastUpdate
    ? (Date.now() - lastUpdate.getTime()) / 1000
    : null;

  return (
    <footer className="statusbar">
      <span>{aircraft.length.toLocaleString()} aircraft</span>

      {anomalies.length > 0 && (
        <span style={{ color: "var(--warn)" }}>
          {anomalies.length} alert{anomalies.length === 1 ? "" : "s"}
        </span>
      )}

      <span>updated {formatAge(ageSeconds)}</span>

      <span className="spacer">{error}</span>
    </footer>
  );
}
