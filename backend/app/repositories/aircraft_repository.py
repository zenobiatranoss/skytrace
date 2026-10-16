from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aircraft import Aircraft
from app.schemas.aircraft import StateVector
from app.utils.time import utcnow


def get_by_icao24(db: Session, icao24: str) -> Aircraft | None:
    return db.scalar(select(Aircraft).where(Aircraft.icao24 == icao24.lower()))


def touch_from_state(
    db: Session,
    state: StateVector,
    now: datetime | None = None,
) -> Aircraft:
    """record that we just heard from this aircraft. creates the row the
    first time, otherwise refreshes the callsign and last_seen."""
    now = now or utcnow()
    aircraft = get_by_icao24(db, state.icao24)

    if aircraft is None:
        aircraft = Aircraft(icao24=state.icao24, first_seen=now, last_seen=now)
        db.add(aircraft)

    if state.callsign:
        aircraft.callsign = state.callsign
    if state.origin_country and not aircraft.country:
        aircraft.country = state.origin_country
    aircraft.last_seen = now
    return aircraft


def apply_metadata(aircraft: Aircraft, meta) -> None:
    """fill in identity details from a reference dataset. only sets what we're
    still missing so live/observed values always win."""
    if not aircraft.registration and meta.registration:
        aircraft.registration = meta.registration
    if not aircraft.type_code and meta.type_code:
        aircraft.type_code = meta.type_code
    if not aircraft.model and meta.model:
        aircraft.model = meta.model
    if not aircraft.operator and meta.operator:
        aircraft.operator = meta.operator


def search(db: Session, query: str, limit: int = 10) -> list[Aircraft]:
    q = query.strip().lower()
    if not q:
        return []

    pattern = f"%{q}%"
    stmt = (
        select(Aircraft)
        .where(
            Aircraft.icao24.like(pattern)
            | Aircraft.registration.ilike(pattern)
            | Aircraft.callsign.ilike(pattern)
        )
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_recent(db: Session, limit: int = 50) -> list[Aircraft]:
    stmt = select(Aircraft).order_by(Aircraft.last_seen.desc()).limit(limit)
    return list(db.scalars(stmt))
