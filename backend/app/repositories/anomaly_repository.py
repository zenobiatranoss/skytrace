from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.utils.time import utcnow


def get_active(db: Session, icao24: str, kind: str) -> Anomaly | None:
    stmt = select(Anomaly).where(
        Anomaly.icao24 == icao24.lower(),
        Anomaly.kind == kind,
        Anomaly.active.is_(True),
    )
    return db.scalar(stmt)


def upsert_active(
    db: Session,
    *,
    icao24: str,
    kind: str,
    severity: str,
    message: str,
    callsign: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    details: str | None = None,
    now: datetime | None = None,
) -> Anomaly:
    """create the anomaly or, if it's already open, just refresh it so we
    keep one row per (aircraft, kind) instead of a row per poll."""
    now = now or utcnow()
    anomaly = get_active(db, icao24, kind)

    if anomaly is None:
        anomaly = Anomaly(
            icao24=icao24.lower(),
            kind=kind,
            severity=severity,
            message=message,
            callsign=callsign,
            latitude=latitude,
            longitude=longitude,
            details=details,
            first_seen=now,
            last_seen=now,
            active=True,
        )
        db.add(anomaly)
        return anomaly

    anomaly.severity = severity
    anomaly.message = message
    anomaly.callsign = callsign or anomaly.callsign
    anomaly.latitude = latitude
    anomaly.longitude = longitude
    anomaly.details = details
    anomaly.last_seen = now
    return anomaly


def resolve(db: Session, anomaly: Anomaly, now: datetime | None = None) -> None:
    anomaly.active = False
    anomaly.resolved_at = now or utcnow()


def resolve_stale(db: Session, cutoff: datetime, now: datetime | None = None) -> int:
    """close anomalies we haven't seen since the cutoff. returns how many."""
    now = now or utcnow()
    open_rows = db.scalars(
        select(Anomaly).where(Anomaly.active.is_(True), Anomaly.last_seen < cutoff)
    ).all()
    for anomaly in open_rows:
        anomaly.active = False
        anomaly.resolved_at = now
    return len(open_rows)


def resolve_all_active(db: Session, now: datetime | None = None) -> int:
    now = now or utcnow()
    result = db.execute(
        update(Anomaly)
        .where(Anomaly.active.is_(True))
        .values(active=False, resolved_at=now)
    )
    return result.rowcount or 0


def list_active(
    db: Session,
    severity: str | None = None,
    kind: str | None = None,
    limit: int = 200,
) -> list[Anomaly]:
    stmt = select(Anomaly).where(Anomaly.active.is_(True))
    if severity:
        stmt = stmt.where(Anomaly.severity == severity)
    if kind:
        stmt = stmt.where(Anomaly.kind == kind)
    stmt = stmt.order_by(Anomaly.last_seen.desc()).limit(limit)
    return list(db.scalars(stmt))


def count_active(
    db: Session,
    severity: str | None = None,
    kind: str | None = None,
) -> int:
    stmt = select(func.count()).select_from(Anomaly).where(Anomaly.active.is_(True))
    if severity:
        stmt = stmt.where(Anomaly.severity == severity)
    if kind:
        stmt = stmt.where(Anomaly.kind == kind)
    return db.scalar(stmt) or 0


def for_aircraft(db: Session, icao24: str, limit: int = 50) -> list[Anomaly]:
    stmt = (
        select(Anomaly)
        .where(Anomaly.icao24 == icao24.lower())
        .order_by(Anomaly.last_seen.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def severity_counts(db: Session) -> dict[str, int]:
    stmt = (
        select(Anomaly.severity, func.count())
        .where(Anomaly.active.is_(True))
        .group_by(Anomaly.severity)
    )
    return {severity: count for severity, count in db.execute(stmt)}


def delete_resolved_before(db: Session, cutoff: datetime) -> int:
    result = db.execute(
        delete(Anomaly).where(
            Anomaly.active.is_(False), Anomaly.last_seen < cutoff
        )
    )
    return result.rowcount or 0
