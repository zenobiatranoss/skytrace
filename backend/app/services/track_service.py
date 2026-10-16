from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.flight import Flight
from app.repositories import track_repository
from app.schemas.aircraft import StateVector
from app.schemas.track import TrackOut, TrackPoint
from app.utils.time import utcnow

# don't store a point for every single update - one a minute is plenty for
# drawing a believable path and keeps the table small
SAMPLE_INTERVAL = timedelta(seconds=60)


class _SampleTracker:
    def __init__(self) -> None:
        self._last: dict[str, datetime] = {}

    def due(self, icao24: str, now: datetime) -> bool:
        last = self._last.get(icao24)
        return last is None or now - last >= SAMPLE_INTERVAL

    def mark(self, icao24: str, now: datetime) -> None:
        self._last[icao24] = now


_samples = _SampleTracker()


def maybe_record(db: Session, flight: Flight, state: StateVector, now: datetime | None = None) -> bool:
    """store a track point if we have coordinates and it's been long enough"""
    if state.latitude is None or state.longitude is None:
        return False

    now = now or utcnow()
    if not _samples.due(state.icao24, now):
        return False

    track_repository.add_point(
        db,
        flight.id,
        latitude=state.latitude,
        longitude=state.longitude,
        altitude=state.altitude_m,
        velocity=state.velocity_ms,
        heading=state.heading,
        recorded_at=state.last_contact or now,
    )
    _samples.mark(state.icao24, now)
    return True


def get_track(db: Session, icao24: str, hours: int = 6) -> TrackOut:
    cutoff = utcnow() - timedelta(hours=hours)
    points: list[TrackPoint] = []

    from sqlalchemy import select

    stmt = (
        select(Flight)
        .where(Flight.icao24 == icao24.lower(), Flight.last_seen >= cutoff)
        .order_by(Flight.first_seen.asc())
    )
    for flight in db.scalars(stmt):
        for row in track_repository.points_for_flight(db, flight.id):
            points.append(
                TrackPoint(
                    latitude=row.latitude,
                    longitude=row.longitude,
                    altitude_m=row.altitude,
                    velocity_ms=row.velocity,
                    heading=row.heading,
                    recorded_at=row.recorded_at,
                )
            )

    return TrackOut(icao24=icao24.lower(), observed=True, points=points)
