import asyncio

from app.providers.adsbdb import AdsbDbProvider


class _Resp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"status {self.status_code}")  # noqa: TRY002

    def json(self):
        return self._payload


class _Client:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.calls = 0

    async def get(self, url):
        self.calls += 1
        return _Resp(self._payload, self.status_code)


ROUTE_PAYLOAD = {
    "response": {
        "flightroute": {
            "callsign": "BAW239",
            "airline": {"name": "British Airways", "icao": "BAW", "iata": "BA"},
            "origin": {
                "icao_code": "EGLL",
                "iata_code": "LHR",
                "name": "London Heathrow Airport",
                "municipality": "London",
                "latitude": 51.4706,
                "longitude": -0.46194,
            },
            "destination": {
                "icao_code": "KBOS",
                "iata_code": "BOS",
                "name": "Logan International Airport",
                "municipality": "Boston",
                "latitude": 42.3643,
                "longitude": -71.0052,
            },
        }
    }
}

AIRCRAFT_PAYLOAD = {
    "response": {
        "aircraft": {
            "mode_s": "400773",
            "type": "777 236ER",
            "icao_type": "B772",
            "manufacturer": "Boeing",
            "registration": "G-VIIV",
            "registered_owner": "British Airways",
            "url_photo": "https://example.com/photo.jpg",
            "url_photo_thumbnail": "https://example.com/thumb.jpg",
        }
    }
}


def test_get_route_parses_airline_and_airports():
    provider = AdsbDbProvider()
    provider._client = _Client(ROUTE_PAYLOAD)

    route = asyncio.run(provider.get_route("baw239"))

    assert route is not None
    assert route.airline == "British Airways"
    assert route.origin.icao == "EGLL"
    assert route.origin.municipality == "London"
    assert route.destination.iata == "BOS"


def test_get_route_returns_none_for_unknown_callsign():
    provider = AdsbDbProvider()
    provider._client = _Client({"response": "unknown callsign"})

    assert asyncio.run(provider.get_route("ZZZ999")) is None


def test_get_aircraft_parses_identity_and_photo():
    provider = AdsbDbProvider()
    provider._client = _Client(AIRCRAFT_PAYLOAD)

    info = asyncio.run(provider.get_aircraft("400773"))

    assert info is not None
    assert info.registration == "G-VIIV"
    assert info.type_code == "B772"
    assert info.model == "Boeing 777 236ER"
    assert info.operator == "British Airways"
    assert info.photo_url == "https://example.com/photo.jpg"


def test_get_aircraft_returns_none_for_unknown():
    provider = AdsbDbProvider()
    provider._client = _Client({"response": "unknown aircraft"})

    assert asyncio.run(provider.get_aircraft("000000")) is None


def test_results_are_cached():
    provider = AdsbDbProvider()
    client = _Client(ROUTE_PAYLOAD)
    provider._client = client

    asyncio.run(provider.get_route("BAW239"))
    asyncio.run(provider.get_route("BAW239"))

    assert client.calls == 1
