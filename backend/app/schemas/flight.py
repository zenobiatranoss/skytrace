from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel
from app.schemas.track import TrackPoint


class FlightOut(ORMModel):
    id: int
    icao24: str
    callsign: str | None = None
    departure_icao: str | None = None
    arrival_icao: str | None = None
    status: str
    first_seen: datetime
    last_seen: datetime


class FlightSummary(BaseModel):
    """one row in an arrivals/departures board. fields stay optional because
    schedule data is far from guaranteed."""

    flight_id: int | None = None
    callsign: str | None = None
    icao24: str
    departure_icao: str | None = None
    arrival_icao: str | None = None
    status: str = "unknown"
    scheduled_time: datetime | None = None
    last_seen: datetime | None = None


class FlightDetail(FlightOut):
    last_latitude: float | None = None
    last_longitude: float | None = None
    last_altitude: float | None = None
    last_velocity: float | None = None
    track: list[TrackPoint] = []
