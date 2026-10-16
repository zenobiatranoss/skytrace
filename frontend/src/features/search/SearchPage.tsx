import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AircraftList } from "../../components/aircraft/AircraftList";
import { useFlightUpdates } from "../../hooks/useFlightUpdates";
import { useAircraft } from "../../hooks/useAircraft";
import { mapSelection } from "../../hooks/useMapSelection";
import { LoadingIndicator } from "../../components/common/LoadingIndicator";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const live = useFlightUpdates();
  const rest = useAircraft();
  const aircraft = live.aircraft.length > 0 ? live.aircraft : rest.aircraft;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return aircraft;
    return aircraft.filter((plane) => {
      const callsign = (plane.callsign ?? "").toLowerCase();
      const reg = (plane.registration ?? "").toLowerCase();
      return (
        plane.icao24.includes(q) || callsign.includes(q) || reg.includes(q)
      );
    });
  }, [aircraft, query]);

  function select(icao24: string) {
    const plane = aircraft.find((p) => p.icao24 === icao24);
    mapSelection.selectAircraft(icao24);
    if (plane && plane.latitude !== null && plane.longitude !== null) {
      mapSelection.focusOn(plane.longitude, plane.latitude, 7);
    }
    navigate("/");
  }

  return (
    <div className="page">
      <div className="page-inner">
        <h2>Aircraft</h2>
        <p style={{ color: "var(--muted)", marginTop: 0 }}>
          Currently tracked aircraft. Use the top search for callsigns,
          registrations and airports.
        </p>

        <input
          type="search"
          value={query}
          placeholder="Filter the list…"
          onChange={(e) => setQuery(e.target.value)}
          style={{
            width: "100%",
            padding: "9px 12px",
            marginBottom: 16,
            background: "var(--panel-2)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            color: "var(--text)",
          }}
        />

        {rest.loading && aircraft.length === 0 ? (
          <LoadingIndicator label="Loading aircraft" />
        ) : (
          <AircraftList aircraft={filtered} onSelect={select} limit={300} />
        )}
      </div>
    </div>
  );
}
