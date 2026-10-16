from fastapi import APIRouter

from app.api.routes import aircraft, airports, anomalies, flights, health, search

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(aircraft.router)
api_router.include_router(airports.router)
api_router.include_router(anomalies.router)
api_router.include_router(flights.router)
api_router.include_router(search.router)

__all__ = ["api_router"]
