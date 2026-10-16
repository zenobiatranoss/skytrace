from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.anomaly import AnomalyList, AnomalyOut
from app.services import anomaly_service

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=AnomalyList)
def list_anomalies(
    severity: str | None = Query(None),
    kind: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AnomalyList:
    items = anomaly_service.list_active(
        db, severity=severity, kind=kind, limit=limit
    )
    total = anomaly_service.count_active(db, severity=severity, kind=kind)
    return AnomalyList(count=total, items=items)


@router.get("/{icao24}", response_model=list[AnomalyOut])
def aircraft_anomalies(
    icao24: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[AnomalyOut]:
    return anomaly_service.for_aircraft(db, icao24, limit=limit)
