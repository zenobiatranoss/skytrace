from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def to_epoch(dt: datetime) -> int:
    return int(dt.timestamp())


def from_epoch(seconds: float | None) -> datetime | None:
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds, tz=UTC)


def age_seconds(dt: datetime | None) -> float | None:
    """seconds since the given time, or None if we have nothing"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return (utcnow() - dt).total_seconds()
