from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.airport import Airport


def get_by_code(db: Session, code: str) -> Airport | None:
    code = code.upper()
    stmt = select(Airport).where((Airport.icao == code) | (Airport.iata == code))
    return db.scalar(stmt)


def upsert(
    db: Session,
    *,
    icao: str | None,
    iata: str | None,
    name: str,
    city: str | None,
    country: str | None,
    latitude: float,
    longitude: float,
    elevation_ft: float | None = None,
) -> Airport:
    existing = None
    if icao:
        existing = db.scalar(select(Airport).where(Airport.icao == icao))
    if existing is None and iata:
        existing = db.scalar(select(Airport).where(Airport.iata == iata))

    if existing is None:
        existing = Airport(latitude=latitude, longitude=longitude)
        db.add(existing)

    existing.icao = icao or existing.icao
    existing.iata = iata or existing.iata
    existing.name = name or existing.name
    existing.city = city or existing.city
    existing.country = country or existing.country
    existing.latitude = latitude
    existing.longitude = longitude
    if elevation_ft is not None:
        existing.elevation_ft = elevation_ft
    return existing
