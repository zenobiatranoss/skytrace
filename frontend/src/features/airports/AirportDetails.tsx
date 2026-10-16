import type { Airport } from "../../types/airport";
import { orUnavailable } from "../../utils/formatters";

export function AirportDetails({ airport }: { airport: Airport }) {
  return (
    <section>
      <div className="field-grid">
        <div className="field">
          <span className="label">ICAO</span>
          <span className="value">{orUnavailable(airport.icao)}</span>
        </div>
        <div className="field">
          <span className="label">IATA</span>
          <span className="value">{orUnavailable(airport.iata)}</span>
        </div>
        <div className="field">
          <span className="label">City</span>
          <span className="value">{orUnavailable(airport.city)}</span>
        </div>
        <div className="field">
          <span className="label">Country</span>
          <span className="value">{orUnavailable(airport.country)}</span>
        </div>
        <div className="field">
          <span className="label">Position</span>
          <span className="value">
            {airport.latitude.toFixed(3)}, {airport.longitude.toFixed(3)}
          </span>
        </div>
        <div className="field">
          <span className="label">Elevation</span>
          <span className="value">
            {airport.elevation_ft !== null
              ? `${Math.round(airport.elevation_ft)} ft`
              : "—"}
          </span>
        </div>
      </div>
    </section>
  );
}
