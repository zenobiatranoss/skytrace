import pytest
from app.cache.response_cache import response_cache
from app.models.flight import Flight
from app.providers.flight_data import RouteInfo
from app.repositories import flight_repository
from app.services import aircraft_service


@pytest.fixture(autouse=True)
def _clean(db):
    # the shared test db keeps committed rows, so start each case blank
    response_cache.clear()
    db.query(Flight).delete()
    db.commit()
    yield
    response_cache.clear()


class _FakeRouteProvider:
    def __init__(self, info: RouteInfo | None) -> None:
        self._info = info
        self.calls = 0

    async def get_route(self, icao24: str) -> RouteInfo | None:
        self.calls += 1
        return self._info


async def test_opensky_route_is_saved_on_the_flight(db, sample_state, monkeypatch):
    response_cache.clear()
    provider = _FakeRouteProvider(RouteInfo("LFPG", "EGLL", "AFR123"))
    monkeypatch.setattr(aircraft_service, "get_route_provider", lambda: provider)

    flight_repository.upsert_active(db, sample_state)
    db.commit()

    route = await aircraft_service._route_info(db, sample_state.icao24)
    assert route.origin.icao == "LFPG"
    assert route.destination.icao == "EGLL"

    # the flight row should now carry the route for the airport boards
    refreshed = flight_repository.get_active_for_aircraft(db, sample_state.icao24)
    assert refreshed.departure_icao == "LFPG"
    assert refreshed.arrival_icao == "EGLL"


async def test_route_is_cached_after_first_lookup(db, sample_state, monkeypatch):
    response_cache.clear()
    provider = _FakeRouteProvider(RouteInfo("LFPG", "EGLL", "AFR123"))
    monkeypatch.setattr(aircraft_service, "get_route_provider", lambda: provider)

    await aircraft_service._route_info(db, sample_state.icao24)
    await aircraft_service._route_info(db, sample_state.icao24)

    assert provider.calls == 1


async def test_no_route_returns_none(db, sample_state, monkeypatch):
    response_cache.clear()
    monkeypatch.setattr(
        aircraft_service, "get_route_provider", lambda: _FakeRouteProvider(None)
    )

    assert await aircraft_service._route_info(db, sample_state.icao24) is None


class _FakeAdsbDb:
    def __init__(self, aircraft=None, route=None) -> None:
        self._aircraft = aircraft
        self._route = route

    async def get_aircraft(self, icao24):
        return self._aircraft

    async def get_route(self, callsign):
        return self._route


async def test_detail_enriches_identity_route_and_photo(db, sample_state, monkeypatch):
    from app.cache.aircraft_cache import aircraft_cache
    from app.core.config import settings
    from app.providers.adsbdb import AircraftInfo, RouteAirport
    from app.providers.adsbdb import RouteInfo as AdsbRoute

    response_cache.clear()
    monkeypatch.setattr(settings, "adsbdb_enabled", True)

    info = AircraftInfo(
        icao24="39de57",
        registration="F-HTVF",
        type_code="A320",
        model="Airbus A320",
        operator="Transavia France",
        photo_url="https://example.com/p.jpg",
        photo_thumbnail="https://example.com/t.jpg",
    )
    route = AdsbRoute(
        callsign="TVF431J",
        airline="Transavia France",
        origin=RouteAirport("LFPG", "CDG", "Paris CDG", None, None, None),
        destination=RouteAirport("EGLL", "LHR", "London Heathrow", None, None, None),
    )
    monkeypatch.setattr(
        aircraft_service,
        "get_adsbdb_provider",
        lambda: _FakeAdsbDb(aircraft=info, route=route),
    )
    aircraft_cache.replace_all([sample_state])

    detail = await aircraft_service.get_detail(db, "39de57")

    assert detail.identity.registration == "F-HTVF"
    assert detail.photo_url == "https://example.com/p.jpg"
    assert detail.airline == "Transavia France"
    assert detail.departure_icao == "LFPG"
    assert detail.departure_iata == "CDG"
    assert detail.arrival_name == "London Heathrow"
