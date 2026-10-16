from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.flight import Flight
from app.models.flight_track import FlightTrack
from app.repositories import anomaly_repository, track_repository
from app.utils.time import utcnow

log = get_logger(__name__)


def purge_old_points(db: Session) -> int:
    """drop track points past the retention window. we don't keep every
    position forever - it adds up fast."""
    cutoff = utcnow() - timedelta(hours=settings.history_retention_hours)
    removed = track_repository.delete_older_than(db, cutoff)
    db.commit()
    return removed


def purge_orphan_flights(db: Session) -> int:
    """flights that never got a track point and are long gone are dead weight"""
    cutoff = utcnow() - timedelta(hours=settings.history_retention_hours)
    subquery = select(FlightTrack.flight_id).distinct()
    stmt = delete(Flight).where(
        Flight.last_seen < cutoff,
        Flight.id.not_in(subquery),
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0


def purge_old_anomalies(db: Session) -> int:
    """resolved anomalies past retention are just noise. open ones stay no
    matter how old they are."""
    cutoff = utcnow() - timedelta(hours=settings.history_retention_hours)
    removed = anomaly_repository.delete_resolved_before(db, cutoff)
    db.commit()
    return removed


def stats(db: Session) -> dict:
    points = db.scalar(select(func.count()).select_from(FlightTrack)) or 0
    flights = db.scalar(select(func.count()).select_from(Flight)) or 0
    return {"track_points": points, "flights": flights}
