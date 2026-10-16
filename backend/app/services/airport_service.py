from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.airport import Airport as AirportModel
from app.providers.airport_data import AirportRecord, get_airport_provider
from app.repositories import airport_repository
from app.schemas.airport import AirportOut


def _from_record(record: AirportRecord) -> AirportOut:
    return AirportOut(
        id=0,
        icao=record.icao,
        iata=record.iata,
        name=record.name,
        city=record.city,
        country=record.country,
        latitude=record.lat,
        longitude=record.lon,
        elevation_ft=record.elevation_ft,
    )


def _from_model(row: AirportModel) -> AirportOut:
    return AirportOut.model_validate(row)


def get_airport(db: Session, code: str) -> AirportOut:
    """db first (things we've already cached), then the airport dataset."""
    row = airport_repository.get_by_code(db, code)
    if row is not None:
        return _from_model(row)

    provider = get_airport_provider()
    provider.load()
    record = provider.get(code)
    if record is None:
        raise NotFoundError(f"airport {code}")
    return _from_record(record)


def cache_from_record(db: Session, record: AirportRecord) -> AirportModel:
    """make sure an airport we reference is persisted for later joins"""
    return airport_repository.upsert(
        db,
        icao=record.icao,
        iata=record.iata,
        name=record.name,
        city=record.city,
        country=record.country,
        latitude=record.lat,
        longitude=record.lon,
        elevation_ft=record.elevation_ft,
    )
