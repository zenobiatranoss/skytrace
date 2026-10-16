import { useEffect, useState } from "react";

import { fetchFlightDetail } from "../../services/flightApi";
import type { FlightDetail } from "../../types/flight";
import { mapSelection } from "../../hooks/useMapSelection";
import { ErrorMessage } from "../../components/common/ErrorMessage";
import { LoadingIndicator } from "../../components/common/LoadingIndicator";
import { FlightTimeline } from "./FlightTimeline";
import { formatAltitude, formatSpeed, formatTime, orUnavailable } from "../../utils/formatters";

export function FlightDetails({ flightId }: { flightId: number }) {
  const [detail, setDetail] = useState<FlightDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchFlightDetail(flightId)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch(() => {
        if (!cancelled) setError(`Could not load flight ${flightId}.`);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [flightId]);

  return (
    <>
      <header>
        <div>
          <div className="title">
            {detail?.callsign || (detail ? detail.icao24 : `Flight ${flightId}`)}
          </div>
          <div className="subtitle">{detail?.icao24}</div>
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
        {loading && <LoadingIndicator label="Loading flight" />}
        {error && <ErrorMessage message={error} />}
        {detail && (
          <>
            <section>
              <div className="route">
                <span>{orUnavailable(detail.departure_icao)}</span>
                <span className="arrow">→</span>
                <span>{orUnavailable(detail.arrival_icao)}</span>
              </div>
              <div className="stat-row">
                <span className="k">Status</span>
                <span className="v">{detail.status}</span>
              </div>
              <div className="stat-row">
                <span className="k">First seen</span>
                <span className="v">{formatTime(detail.first_seen)}</span>
              </div>
              <div className="stat-row">
                <span className="k">Last seen</span>
                <span className="v">{formatTime(detail.last_seen)}</span>
              </div>
              <div className="stat-row">
                <span className="k">Last altitude</span>
                <span className="v">{formatAltitude(detail.last_altitude)}</span>
              </div>
              <div className="stat-row">
                <span className="k">Last speed</span>
                <span className="v">{formatSpeed(detail.last_velocity)}</span>
              </div>
            </section>

            <section>
              <h3>Recent positions</h3>
              <FlightTimeline points={detail.track} />
            </section>
          </>
        )}
      </div>
    </>
  );
}
