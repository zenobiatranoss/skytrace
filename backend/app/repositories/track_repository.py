from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.flight_track import FlightTrack


def add_point(
    db: Session,
    flight_id: int,
    *,
    latitude: float,
    longitude: float,
    altitude: float | None = None,
    velocity: float | None = None,
    heading: float | None = None,
    recorded_at: datetime | None = None,
) -> FlightTrack:
    point = FlightTrack(
        flight_id=flight_id,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        velocity=velocity,
        heading=heading,
    )
    if recorded_at:
        point.recorded_at = recorded_at
    db.add(point)
    return point


def points_for_flight(db: Session, flight_id: int, limit: int = 2000) -> list[FlightTrack]:
    stmt = (
        select(FlightTrack)
        .where(FlightTrack.flight_id == flight_id)
        .order_by(FlightTrack.recorded_at.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def delete_older_than(db: Session, cutoff: datetime) -> int:
    result = db.execute(
        delete(FlightTrack).where(FlightTrack.recorded_at < cutoff)
    )
    return result.rowcount or 0
