from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.time import utcnow


class FlightTrack(Base):
    """one recorded position sample. we don't keep every update forever -
    the cleanup task trims these on a schedule."""

    __tablename__ = "flight_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), index=True)

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    altitude: Mapped[float | None] = mapped_column(Float)
    velocity: Mapped[float | None] = mapped_column(Float)
    heading: Mapped[float | None] = mapped_column(Float)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, index=True
    )

    flight: Mapped["Flight"] = relationship(back_populates="points")
