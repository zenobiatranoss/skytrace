from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.flight import FlightDetail, FlightSummary
from app.services import flight_service

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("", response_model=list[FlightSummary])
def list_flights(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[FlightSummary]:
    return flight_service.list_active(db, limit=limit)


@router.get("/{flight_id}", response_model=FlightDetail)
def get_flight(flight_id: int, db: Session = Depends(get_db)) -> FlightDetail:
    return flight_service.get_detail(db, flight_id)
