from datetime import datetime

from pydantic import BaseModel


class TrackPoint(BaseModel):
    latitude: float
    longitude: float
    altitude_m: float | None = None
    velocity_ms: float | None = None
    heading: float | None = None
    recorded_at: datetime


class TrackOut(BaseModel):
    icao24: str
    callsign: str | None = None
    # true when the line is something we actually observed, not a guess
    observed: bool = True
    points: list[TrackPoint] = []
