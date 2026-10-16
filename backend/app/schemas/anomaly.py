from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AnomalyOut(ORMModel):
    id: int | None = None
    icao24: str
    callsign: str | None = None
    kind: str
    severity: str
    message: str
    latitude: float | None = None
    longitude: float | None = None
    first_seen: datetime
    last_seen: datetime
    active: bool = True


class AnomalyList(BaseModel):
    count: int
    items: list[AnomalyOut]
