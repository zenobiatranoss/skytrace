from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.flight import Flight
from app.schemas.aircraft import StateVector
from app.utils.time import utcnow

# a flight is considered dropped if we haven't heard from it in this long
ACTIVE_WINDOW = timedelta(hours=2)


def get_by_id(db: Session, flight_id: int) -> Flight | None:
    return db.get(Flight, flight_id)


def get_active_for_aircraft(db: Session, icao24: str) -> Flight | None:
    cutoff = utcnow() - ACTIVE_WINDOW
    stmt = (
        select(Flight)
        .where(Flight.icao24 == icao24.lower(), Flight.last_seen >= cutoff)
        .order_by(Flight.last_seen.desc())
    )
    return db.scalar(stmt)


def upsert_active(
    db: Session,
    state: StateVector,
    now: datetime | None = None,
    departure_icao: str | None = None,
    arrival_icao: str | None = None,
) -> Flight:
    """follow the current flight of an aircraft, updating its last known
    position and filling in the route once we learn it."""
    now = now or utcnow()
    flight = get_active_for_aircraft(db, state.icao24)

    if flight is None:
        flight = Flight(
            icao24=state.icao24,
            callsign=state.callsign,
            first_seen=now,
            last_seen=now,
        )
        db.add(flight)
    else:
        # a new callsign on the same frame usually means a new leg
        if state.callsign and flight.callsign and state.callsign != flight.callsign:
            flight = Flight(
                icao24=state.icao24,
                callsign=state.callsign,
                first_seen=now,
                last_seen=now,
            )
            db.add(flight)
        elif state.callsign:
            flight.callsign = state.callsign

    flight.last_seen = now
    flight.last_latitude = state.latitude
    flight.last_longitude = state.longitude
    flight.last_altitude = state.altitude_m
    flight.last_velocity = state.velocity_ms

    if departure_icao:
        flight.departure_icao = departure_icao
    if arrival_icao:
        flight.arrival_icao = arrival_icao

    from app.utils.flight_status import derive_status

    flight.status = derive_status(state.on_ground, None, 3600).value
    return flight


def list_active(db: Session, limit: int = 100) -> list[Flight]:
    cutoff = utcnow() - ACTIVE_WINDOW
    stmt = (
        select(Flight)
        .where(Flight.last_seen >= cutoff)
        .order_by(Flight.last_seen.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def search(db: Session, query: str, limit: int = 10) -> list[Flight]:
    q = query.strip().lower()
    if not q:
        return []
    pattern = f"%{q}%"
    stmt = (
        select(Flight)
        .where(Flight.callsign.ilike(pattern) | Flight.icao24.like(pattern))
        .order_by(Flight.last_seen.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))
