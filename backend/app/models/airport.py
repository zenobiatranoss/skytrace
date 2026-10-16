from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Airport(Base):
    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(primary_key=True)
    icao: Mapped[str | None] = mapped_column(String(4), index=True)
    iata: Mapped[str | None] = mapped_column(String(3), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    city: Mapped[str | None] = mapped_column(String(64))
    country: Mapped[str | None] = mapped_column(String(64))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    elevation_ft: Mapped[float | None] = mapped_column(Float)

    def __repr__(self) -> str:
        return f"<Airport {self.icao or self.iata} {self.name}>"
