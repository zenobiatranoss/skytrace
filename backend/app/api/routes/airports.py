from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.airport import AirportOut
from app.schemas.flight import FlightSummary
from app.services import airport_service, flight_service

router = APIRouter(prefix="/airports", tags=["airports"])


@router.get("/{code}", response_model=AirportOut)
def get_airport(code: str, db: Session = Depends(get_db)) -> AirportOut:
    return airport_service.get_airport(db, code)


@router.get("/{code}/arrivals", response_model=list[FlightSummary])
def arrivals(
    code: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[FlightSummary]:
    return flight_service.arrivals(db, code, limit=limit)


@router.get("/{code}/departures", response_model=list[FlightSummary])
def departures(
    code: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[FlightSummary]:
    return flight_service.departures(db, code, limit=limit)
