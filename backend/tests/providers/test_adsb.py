import asyncio

from app.providers.adsb import AdsbFiProvider, AdsbLolProvider
from app.utils.time import utcnow


def _provider_with(payload, *, military=None):
    provider = AdsbLolProvider()

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return payload

    class _Client:
        def __init__(self):
            self.urls: list[str] = []

        async def get(self, url):
            self.urls.append(url)
            if url.endswith("/v2/mil"):
                return _Resp() if military is None else military()
            return _Resp()

    provider._client = _Client()
    return provider


def test_parse_aircraft_maps_readsb_fields():
    provider = AdsbLolProvider()
    now = utcnow()
    row = {
        "hex": "39de57",
        "flight": "TVF431J ",
        "lat": 54.2975,
        "lon": 10.928,
        "alt_baro": 38000,
        "alt_geom": 38600,
        "gs": 447.0,
        "track": 218.89,
        "baro_rate": -640,
        "squawk": "4221",
        "seen": 1.2,
        "seen_pos": 0.8,
    }

    state = provider._parse_aircraft(row, now)

    assert state is not None
    assert state.icao24 == "39de57"
    assert state.callsign == "TVF431J"
    assert state.latitude == 54.2975
    assert state.longitude == 10.928
    assert round(state.altitude_m) == round(38000 * 0.3048)
    assert round(state.geo_altitude_m) == round(38600 * 0.3048)
    assert round(state.velocity_ms, 2) == round(447.0 * 0.514444, 2)
    assert state.heading == 218.89
    assert round(state.vertical_rate_ms, 3) == round(-640 * 0.00508, 3)
    assert state.squawk == "4221"
    assert state.on_ground is False
    # seen_pos (0.8s) is fresher than seen (1.2s)
    assert state.last_contact < state.time_position


def test_parse_aircraft_marks_ground():
    provider = AdsbLolProvider()
    state = provider._parse_aircraft(
        {"hex": "abc123", "lat": 1.0, "lon": 2.0, "alt_baro": "ground"},
        utcnow(),
    )

    assert state is not None
    assert state.on_ground is True
    assert state.altitude_m is None


def test_parse_aircraft_skips_bad_hex():
    provider = AdsbLolProvider()
    assert provider._parse_aircraft({"hex": "nope"}, utcnow()) is None


def test_fetch_states_builds_point_url_from_bounds():
    provider = _provider_with({"ac": []})
    asyncio.run(provider.fetch_states((50.0, -1.0, 52.0, 1.0)))

    urls = provider._client.urls
    assert len(urls) == 1
    assert urls[0].startswith("https://api.adsb.lol/v2/point/51.0000/0.0000/")


def test_fetch_states_skips_without_area(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "adsb_center", "")
    provider = _provider_with({"ac": []})

    assert asyncio.run(provider.fetch_states(None)) == []
    assert provider._client.urls == []


def test_fetch_states_uses_center_when_no_bounds(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "adsb_center", "51.5,-0.1")
    monkeypatch.setattr(settings, "adsb_radius_nm", 100)
    provider = _provider_with({"ac": []})

    asyncio.run(provider.fetch_states(None))

    assert provider._client.urls == ["https://api.adsb.lol/v2/point/51.5000/-0.1000/100"]


def test_fetch_states_tolerates_one_dead_feed(monkeypatch):
    from app.core.config import settings
    from app.core.errors import ProviderError

    monkeypatch.setattr(settings, "adsb_military", True)
    provider = AdsbLolProvider()

    payload = {
        "now": 1690000000000,
        "ac": [{"hex": "abc123", "lat": 1.0, "lon": 2.0, "alt_baro": 1000}],
    }

    def _mil_fail():
        raise ProviderError("adsb", "mil down")

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    class _Client:
        async def get(self, url):
            if url.endswith("/v2/mil"):
                return _mil_fail()
            return _Resp()

    provider._client = _Client()

    states = asyncio.run(provider.fetch_states((50.0, -1.0, 52.0, 1.0)))

    assert [s.icao24 for s in states] == ["abc123"]


def test_adsbfi_reads_aircraft_key_and_path():
    provider = AdsbFiProvider()

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "now": 1690000000000,
                "aircraft": [{"hex": "abc123", "lat": 1.0, "lon": 2.0, "alt_baro": 1000}],
            }

    class _Client:
        def __init__(self):
            self.urls: list[str] = []

        async def get(self, url):
            self.urls.append(url)
            return _Resp()

    provider._client = _Client()

    states = asyncio.run(provider.fetch_states((50.0, -1.0, 52.0, 1.0)))

    assert [s.icao24 for s in states] == ["abc123"]
    assert provider._client.urls[0].startswith("https://opendata.adsb.fi/api/v2/lat/")


def test_adsbfi_skips_area_beyond_its_radius(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "adsb_center", "0,0")
    monkeypatch.setattr(settings, "adsb_radius_nm", 20000)
    provider = AdsbFiProvider()

    class _Client:
        def __init__(self):
            self.urls: list[str] = []

        async def get(self, url):
            self.urls.append(url)

    provider._client = _Client()

    assert asyncio.run(provider.fetch_states(None)) == []
    assert provider._client.urls == []
