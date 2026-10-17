from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.flight import Flight
from app.repositories import flight_repository, track_repository
from app.schemas.flight import FlightDetail, FlightSummary
from app.schemas.track import TrackPoint


def list_active(db: Session, limit: int = 100) -> list[FlightSummary]:
    rows = flight_repository.list_active(db, limit=limit)
    return [_to_summary(f) for f in rows]


def _to_summary(flight: Flight) -> FlightSummary:
    return FlightSummary(
        flight_id=flight.id,
        callsign=flight.callsign,
        icao24=flight.icao24,
        departure_icao=flight.departure_icao,
        arrival_icao=flight.arrival_icao,
        status=flight.status,
        last_seen=flight.last_seen,
    )


def get_detail(db: Session, flight_id: int) -> FlightDetail:
    flight = flight_repository.get_by_id(db, flight_id)
    if flight is None:
        raise NotFoundError(f"flight {flight_id}")

    points = [
        TrackPoint(
            latitude=p.latitude,
            longitude=p.longitude,
            altitude_m=p.altitude,
            velocity_ms=p.velocity,
            heading=p.heading,
            recorded_at=p.recorded_at,
        )
        for p in track_repository.points_for_flight(db, flight.id)
    ]

    return FlightDetail(
        id=flight.id,
        icao24=flight.icao24,
        callsign=flight.callsign,
        departure_icao=flight.departure_icao,
        arrival_icao=flight.arrival_icao,
        status=flight.status,
        first_seen=flight.first_seen,
        last_seen=flight.last_seen,
        last_latitude=flight.last_latitude,
        last_longitude=flight.last_longitude,
        last_altitude=flight.last_altitude,
        last_velocity=flight.last_velocity,
        track=points,
    )


def _board(db: Session, code: str, column: str, limit: int) -> list[FlightSummary]:
    code = code.upper()
    field = getattr(Flight, column)
    stmt = (
        select(Flight)
        .where(field == code)
        .order_by(Flight.last_seen.desc())
        .limit(limit)
    )
    return [_to_summary(f) for f in db.scalars(stmt)]


def arrivals(db: Session, icao: str, limit: int = 50) -> list[FlightSummary]:
    return _board(db, icao, "arrival_icao", limit)


def departures(db: Session, icao: str, limit: int = 50) -> list[FlightSummary]:
    return _board(db, icao, "departure_icao", limit)
