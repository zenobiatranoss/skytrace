import { useState } from "react";

import { AirportFlights } from "../../components/airports/AirportFlights";
import type { FlightSummary } from "../../types/flight";

interface Props {
  arrivals: FlightSummary[];
  departures: FlightSummary[];
  onSelect: (flightId: number) => void;
}

type Tab = "arrivals" | "departures";

export function ArrivalDepartures({ arrivals, departures, onSelect }: Props) {
  const [tab, setTab] = useState<Tab>("arrivals");

  return (
    <section>
      <div className="tab-bar">
        <button
          type="button"
          className={tab === "arrivals" ? "active" : undefined}
          onClick={() => setTab("arrivals")}
        >
          Arrivals ({arrivals.length})
        </button>
        <button
          type="button"
          className={tab === "departures" ? "active" : undefined}
          onClick={() => setTab("departures")}
        >
          Departures ({departures.length})
        </button>
      </div>

      {tab === "arrivals" ? (
        <AirportFlights
          flights={arrivals}
          emptyText="No arriving flights observed yet."
          onSelect={onSelect}
        />
      ) : (
        <AirportFlights
          flights={departures}
          emptyText="No departing flights observed yet."
          onSelect={onSelect}
        />
      )}
    </section>
  );
}
