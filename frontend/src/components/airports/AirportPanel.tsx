import { useAirports } from "../../hooks/useAirports";
import { mapSelection } from "../../hooks/useMapSelection";
import { ErrorMessage } from "../common/ErrorMessage";
import { LoadingIndicator } from "../common/LoadingIndicator";
import { AirportDetails } from "../../features/airports/AirportDetails";
import { ArrivalDepartures } from "../../features/airports/ArrivalDepartures";

export function AirportPanel({ code }: { code: string }) {
  const { airport, arrivals, departures, loading, error } = useAirports(code);

  return (
    <>
      <header>
        <div>
          <div className="title">{airport?.name ?? code.toUpperCase()}</div>
          <div className="subtitle">
            {[airport?.icao, airport?.iata, airport?.city]
              .filter(Boolean)
              .join(" · ") || "Airport"}
          </div>
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
        {loading && <LoadingIndicator label="Loading airport" />}
        {error && <ErrorMessage message={error} />}
        {airport && (
          <>
            <AirportDetails airport={airport} />
            <ArrivalDepartures
              arrivals={arrivals}
              departures={departures}
              onSelect={(id) => mapSelection.selectFlight(String(id))}
            />
          </>
        )}
      </div>
    </>
  );
}
