import { useEffect, useState } from "react";

import { fetchAircraftDetail } from "../../services/aircraftApi";
import { fetchTrack } from "../../services/flightApi";
import type { AircraftDetail } from "../../types/aircraft";
import type { Track } from "../../types/flight";
import { mapSelection } from "../../hooks/useMapSelection";
import { ErrorMessage } from "../common/ErrorMessage";
import { LoadingIndicator } from "../common/LoadingIndicator";
import { AircraftDetails, AircraftStatusBadge } from "../../features/aircraft/AircraftDetails";
import { AircraftAnomalies } from "../../features/anomalies/AircraftAnomalies";

export function AircraftPanel({ icao24 }: { icao24: string }) {
  const [detail, setDetail] = useState<AircraftDetail | null>(null);
  const [track, setTrack] = useState<Track | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function load() {
      try {
        const [detailData, trackData] = await Promise.all([
          fetchAircraftDetail(icao24),
          fetchTrack(icao24).catch(() => null),
        ]);
        if (cancelled) return;
        setDetail(detailData);
        setTrack(trackData);
      } catch {
        if (!cancelled) setError(`Could not load aircraft ${icao24}.`);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    // refresh the panel while it's open so the numbers stay current
    const timer = window.setInterval(load, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [icao24]);

  const title = detail?.identity.callsign || detail?.identity.registration || icao24;

  return (
    <>
      <header>
        <div>
          <div className="title">{title}</div>
          <div className="subtitle">
            {icao24}
            {detail?.identity.registration
              ? ` · ${detail.identity.registration}`
              : ""}
          </div>
          {detail && (
            <div style={{ marginTop: 6 }}>
              <AircraftStatusBadge detail={detail} />
            </div>
          )}
        </div>
        <button
          className="close"
          aria-label="Close"
          onClick={() => mapSelection.clear()}
        >
          ×
        </button>
      </header>

      <div className="body">
        {loading && !detail && <LoadingIndicator label="Loading aircraft" />}
        {error && <ErrorMessage message={error} />}
        {detail && <AircraftDetails detail={detail} track={track} />}
        {detail && (
          <section>
            <h3>Alerts</h3>
            <AircraftAnomalies icao24={icao24} />
          </section>
        )}
      </div>
    </>
  );
}
