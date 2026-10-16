import type { FlightSummary } from "../../types/flight";
import { formatTime, orUnavailable } from "../../utils/formatters";

interface Props {
  flights: FlightSummary[];
  emptyText: string;
  onSelect: (flightId: number) => void;
}

export function AirportFlights({ flights, emptyText, onSelect }: Props) {
  if (flights.length === 0) {
    return <p className="empty-note">{emptyText}</p>;
  }

  return (
    <table className="flight-table">
      <thead>
        <tr>
          <th>Flight</th>
          <th>From</th>
          <th>To</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody>
        {flights.map((flight) => (
          <tr
            key={`${flight.flight_id}-${flight.icao24}`}
            onClick={() => flight.flight_id && onSelect(flight.flight_id)}
            style={{ cursor: flight.flight_id ? "pointer" : "default" }}
          >
            <td>{flight.callsign || flight.icao24}</td>
            <td>{orUnavailable(flight.departure_icao)}</td>
            <td>{orUnavailable(flight.arrival_icao)}</td>
            <td>{formatTime(flight.last_seen)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
