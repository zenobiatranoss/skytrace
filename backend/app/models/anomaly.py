from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.time import utcnow


class Anomaly(Base):
    """a flagged behaviour we observed on an aircraft.

    rows are kept after they resolve so there's a trail to look back on.
    active=false simply means we stopped seeing the condition."""

    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True)
    icao24: Mapped[str] = mapped_column(String(6), index=True)
    callsign: Mapped[str | None] = mapped_column(String(16))

    kind: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    message: Mapped[str] = mapped_column(Text)

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    # detector-specific numbers, kept as json so we don't add a column per rule
    details: Mapped[str | None] = mapped_column(Text)

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<Anomaly {self.icao24} {self.kind} {self.severity}>"
