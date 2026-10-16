from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.flight_track import FlightTrack


class Flight(Base):
    """a journey we've observed. departure/arrival come from route data when we
    can get it, otherwise they stay null instead of being guessed at."""

    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(primary_key=True)
    icao24: Mapped[str] = mapped_column(String(6), index=True)
    callsign: Mapped[str | None] = mapped_column(String(16), index=True)

    departure_icao: Mapped[str | None] = mapped_column(String(4))
    arrival_icao: Mapped[str | None] = mapped_column(String(4))

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(16), default="unknown")

    # where we last heard the aircraft
    last_latitude: Mapped[float | None] = mapped_column(Float)
    last_longitude: Mapped[float | None] = mapped_column(Float)
    last_altitude: Mapped[float | None] = mapped_column(Float)
    last_velocity: Mapped[float | None] = mapped_column(Float)

    points: Mapped[list["FlightTrack"]] = relationship(
        back_populates="flight",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Flight {self.callsign or self.icao24} {self.status}>"
