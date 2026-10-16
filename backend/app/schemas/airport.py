from app.schemas.common import ORMModel


class AirportOut(ORMModel):
    id: int
    icao: str | None = None
    iata: str | None = None
    name: str
    city: str | None = None
    country: str | None = None
    latitude: float
    longitude: float
    elevation_ft: float | None = None


class AirportSummary(ORMModel):
    """lighter payload for map markers and search results"""

    icao: str | None = None
    iata: str | None = None
    name: str
    city: str | None = None
    country: str | None = None
    latitude: float
    longitude: float
