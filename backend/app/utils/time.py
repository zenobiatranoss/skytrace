from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_epoch(dt: datetime) -> int:
    return int(dt.timestamp())


def from_epoch(seconds: int | float | None) -> datetime | None:
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def age_seconds(dt: datetime | None) -> float | None:
    """seconds since the given time, or None if we have nothing"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (utcnow() - dt).total_seconds()
