"""Coordinates anomaly detection.

Pure rule logic lives in anomaly_rules; this module owns the bits that need
state - a short in-memory movement history per aircraft, and the database
round-trip that keeps the anomaly trail.

One row is kept per (aircraft, kind): while a condition holds we refresh it,
and once we stop seeing it for the hold window it's closed rather than
deleted, so there's something to look back on.
"""

import json
from collections import deque
from datetime import timedelta

from sqlalchemy.orm import Session

from app.cache.aircraft_cache import aircraft_cache
from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.repositories import anomaly_repository
from app.schemas.aircraft import StateVector
from app.schemas.anomaly import AnomalyOut
from app.services.anomaly_rules import Signal, TrackSample, evaluate
from app.utils.time import utcnow

log = get_logger(__name__)

_history: dict[str, deque[TrackSample]] = {}
_active_views: list[AnomalyOut] = []


def detect(states: list[StateVector]) -> dict[str, list[Signal]]:
    """evaluate every state against the detectors, updating our short
    movement history as we go. returns signals keyed by icao24."""
    if not states:
        return {}

    now = utcnow()
    window_start = now.timestamp() - settings.anomaly_history_minutes * 60
    current: dict[str, list[Signal]] = {}
    seen: set[str] = set()

    for state in states:
        seen.add(state.icao24)
        history = _history.setdefault(state.icao24, deque())
        while history and history[0].at < window_start:
            history.popleft()

        prev = history[-1] if history else None
        if state.latitude is not None and state.longitude is not None:
            # a repeated fix is the feed re-serving one position, not movement.
            # keeping it would fake loitering and jam the history with copies.
            moved = (
                prev is None
                or state.latitude != prev.latitude
                or state.longitude != prev.longitude
            )
            if moved:
                at = (
                    state.last_contact.timestamp()
                    if state.last_contact
                    else now.timestamp()
                )
                history.append(
                    TrackSample(
                        latitude=state.latitude,
                        longitude=state.longitude,
                        at=at,
                        altitude=state.altitude_m,
                        velocity=state.velocity_ms,
                        position_at=(
                            state.time_position.timestamp()
                            if state.time_position
                            else None
                        ),
                    )
                )

        signals = evaluate(state, list(history), prev)
        if signals:
            current[state.icao24] = signals

    # forget aircraft that dropped off the feed, otherwise the dict grows
    for icao24 in [k for k in _history if k not in seen]:
        del _history[icao24]

    return current


def _persist(current: dict[str, list[Signal]]) -> list[AnomalyOut]:
    db = SessionLocal()
    try:
        now = utcnow()
        for icao24, signals in current.items():
            state = aircraft_cache.get(icao24)
            for signal in signals:
                anomaly_repository.upsert_active(
                    db,
                    icao24=icao24,
                    kind=signal.kind,
                    severity=str(signal.severity),
                    message=signal.message,
                    callsign=state.callsign if state else None,
                    latitude=state.latitude if state else None,
                    longitude=state.longitude if state else None,
                    details=json.dumps(signal.details) if signal.details else None,
                    now=now,
                )

        # anything we didn't refresh within the hold window is closed
        cutoff = now - timedelta(seconds=settings.anomaly_hold_seconds)
        anomaly_repository.resolve_stale(db, cutoff, now=now)
        db.commit()

        return [
            AnomalyOut.model_validate(row)
            for row in anomaly_repository.list_active(db, limit=500)
        ]
    except Exception:
        db.rollback()
        log.exception("anomaly persist failed")
        return _active_views
    finally:
        db.close()


def evaluate_cycle(states: list[StateVector]) -> list[AnomalyOut]:
    """detect + persist in one go. safe to call from a worker thread."""
    global _active_views

    if not states:
        # don't close everything just because one poll came back empty
        return _active_views

    current = detect(states)
    _active_views = _persist(current)
    return _active_views


def reset(db: Session) -> int:
    """close anything left open from a previous run - we re-detect on the
    next cycle anyway."""
    global _active_views
    _history.clear()
    _active_views = []
    closed = anomaly_repository.resolve_all_active(db)
    db.commit()
    return closed


def list_active(
    db: Session,
    severity: str | None = None,
    kind: str | None = None,
    limit: int = 200,
) -> list[AnomalyOut]:
    rows = anomaly_repository.list_active(
        db, severity=severity, kind=kind, limit=limit
    )
    return [AnomalyOut.model_validate(row) for row in rows]


def for_aircraft(db: Session, icao24: str, limit: int = 50) -> list[AnomalyOut]:
    rows = anomaly_repository.for_aircraft(db, icao24, limit=limit)
    return [AnomalyOut.model_validate(row) for row in rows]


def count_active(
    db: Session,
    severity: str | None = None,
    kind: str | None = None,
) -> int:
    return anomaly_repository.count_active(db, severity=severity, kind=kind)


def severity_counts(db: Session) -> dict[str, int]:
    return anomaly_repository.severity_counts(db)
