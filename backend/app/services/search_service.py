from sqlalchemy.orm import Session

from app.cache.aircraft_cache import aircraft_cache
from app.providers.airport_data import get_airport_provider
from app.repositories import aircraft_repository, flight_repository
from app.schemas.search import SearchResponse, SearchResult


def _aircraft_results(db: Session, query: str, limit: int) -> list[SearchResult]:
    results: list[SearchResult] = []
    seen: set[str] = set()

    # live cache knows about everything currently airborne
    q = query.strip().lower()
    for state in aircraft_cache.all():
        if len(results) >= limit:
            break
        callsign = (state.callsign or "").lower()
        if q in state.icao24 or (callsign and q in callsign):
            seen.add(state.icao24)
            results.append(
                SearchResult(
                    kind="aircraft",
                    id=state.icao24,
                    label=state.callsign or state.icao24,
                    subtitle=state.origin_country,
                    latitude=state.latitude,
                    longitude=state.longitude,
                )
            )

    # then anything stored, matched on registration too
    for row in aircraft_repository.search(db, query, limit=limit):
        if row.icao24 in seen or len(results) >= limit:
            continue
        results.append(
            SearchResult(
                kind="aircraft",
                id=row.icao24,
                label=row.callsign or row.registration or row.icao24,
                subtitle=row.registration,
            )
        )
    return results


def _airport_results(query: str, limit: int) -> list[SearchResult]:
    provider = get_airport_provider()
    provider.load()
    return [
        SearchResult(
            kind="airport",
            id=record.icao or record.iata or record.name,
            label=record.name,
            subtitle=" ".join(
                filter(None, [record.iata, record.city, record.country])
            )
            or None,
            latitude=record.lat,
            longitude=record.lon,
        )
        for record in provider.search(query, limit=limit)
    ]


def _flight_results(db: Session, query: str, limit: int) -> list[SearchResult]:
    return [
        SearchResult(
            kind="flight",
            id=str(flight.id),
            label=flight.callsign or flight.icao24,
            subtitle=f"{flight.departure_icao or '?'} → {flight.arrival_icao or '?'}",
        )
        for flight in flight_repository.search(db, query, limit=limit)
    ]


def search(db: Session, query: str, limit: int = 10) -> SearchResponse:
    query = query.strip()
    if not query:
        return SearchResponse(query=query, results=[])

    results: list[SearchResult] = []
    results += _aircraft_results(db, query, limit)
    results += _airport_results(query, limit)
    results += _flight_results(db, query, limit)

    return SearchResponse(query=query, results=results[:limit * 3])
