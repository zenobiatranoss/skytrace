from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.time import utcnow


class Aircraft(Base):
    """identity data about a frame, keyed by the 24-bit icao address"""

    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(primary_key=True)
    icao24: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    registration: Mapped[str | None] = mapped_column(String(16))
    callsign: Mapped[str | None] = mapped_column(String(16))
    type_code: Mapped[str | None] = mapped_column(String(8))
    model: Mapped[str | None] = mapped_column(String(64))
    operator: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(64))

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    def __repr__(self) -> str:
        return f"<Aircraft {self.icao24} {self.callsign or ''}>"
