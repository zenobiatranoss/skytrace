import type { AircraftDetail } from "../../types/aircraft";
import type { Track } from "../../types/flight";
import { statusColor, statusLabel } from "../../utils/flightStatus";
import {
  formatAge,
  formatAltitude,
  formatCoords,
  formatHeading,
  formatSpeed,
  formatVerticalRate,
  orUnavailable,
} from "../../utils/formatters";
import { FlightHistory } from "../flights/FlightHistory";

interface Props {
  detail: AircraftDetail;
  track: Track | null;
}

export function AircraftDetails({ detail, track }: Props) {
  const { identity, position } = detail;
  const hasRoute = detail.departure_icao || detail.arrival_icao;
  const departed = detail.departure_iata ?? detail.departure_icao;
  const arrived = detail.arrival_iata ?? detail.arrival_icao;
  const routeNames = [detail.departure_name, detail.arrival_name].filter(Boolean);
  const photo = detail.photo_url ?? detail.photo_thumbnail;

  return (
    <>
      {photo && (
        <section className="aircraft-photo">
          <a href={photo} target="_blank" rel="noreferrer">
            <img
              src={photo}
              alt={identity.registration ?? identity.icao24}
              loading="lazy"
              referrerPolicy="no-referrer"
            />
          </a>
        </section>
      )}

      <section>
        <div className="route">
          <span>{orUnavailable(departed)}</span>
          <span className="arrow">→</span>
          <span>{orUnavailable(arrived)}</span>
        </div>
        {routeNames.length === 2 && (
          <p className="route-names">
            {routeNames[0]} → {routeNames[1]}
          </p>
        )}
        {detail.airline && <p className="route-airline">{detail.airline}</p>}
        {!hasRoute && (
          <p className="empty-note">Route not available from the data source.</p>
        )}
      </section>

      <section>
        <h3>Movement</h3>
        <div className="field-grid">
          <div className="field">
            <span className="label">Altitude</span>
            <span className="value">{formatAltitude(position?.altitude_m ?? null)}</span>
          </div>
          <div className="field">
            <span className="label">Speed</span>
            <span className="value">{formatSpeed(position?.velocity_ms ?? null)}</span>
          </div>
          <div className="field">
            <span className="label">Heading</span>
            <span className="value">{formatHeading(position?.heading ?? null)}</span>
          </div>
          <div className="field">
            <span className="label">Vertical rate</span>
            <span className="value">
              {formatVerticalRate(position?.vertical_rate_ms ?? null)}
            </span>
          </div>
          <div className="field">
            <span className="label">Position</span>
            <span className="value">
              {formatCoords(position?.latitude ?? null, position?.longitude ?? null)}
            </span>
          </div>
          <div className="field">
            <span className="label">Squawk</span>
            <span className="value">{orUnavailable(position?.squawk ?? null)}</span>
          </div>
        </div>
      </section>

      <section>
        <h3>Identity</h3>
        <div className="stat-row">
          <span className="k">Registration</span>
          <span className="v">{orUnavailable(identity.registration)}</span>
        </div>
        <div className="stat-row">
          <span className="k">Type</span>
          <span className="v">{orUnavailable(identity.type_code)}</span>
        </div>
        <div className="stat-row">
          <span className="k">Model</span>
          <span className="v">{orUnavailable(identity.model)}</span>
        </div>
        <div className="stat-row">
          <span className="k">Operator</span>
          <span className="v">{orUnavailable(identity.operator)}</span>
        </div>
        <div className="stat-row">
          <span className="k">Country</span>
          <span className="v">{orUnavailable(identity.country)}</span>
        </div>
      </section>

      <section>
        <h3>Observed path</h3>
        <FlightHistory track={track} />
      </section>
    </>
  );
}

export function AircraftStatusBadge({ detail }: { detail: AircraftDetail }) {
  return (
    <span
      className="badge"
      style={{
        background: `${statusColor(detail.status)}22`,
        color: statusColor(detail.status),
      }}
    >
      {statusLabel(detail.status)} · {formatAge(detail.age_seconds)}
    </span>
  );
}
