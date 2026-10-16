import asyncio

from app.providers.opensky import OpenSkyProvider


class _Resp:
    def raise_for_status(self):
        return None

    def json(self):
        return {"states": []}


class _Client:
    def __init__(self):
        self.last_params = None

    async def get(self, url, params=None, headers=None):
        self.last_params = params
        return _Resp()


def test_fetch_states_sends_bounds_as_query():
    provider = OpenSkyProvider()
    provider._client = _Client()

    states = asyncio.run(provider.fetch_states((35.0, -12.0, 60.0, 30.0)))

    assert states == []
    assert provider._client.last_params == {
        "lamin": 35.0,
        "lomin": -12.0,
        "lamax": 60.0,
        "lomax": 30.0,
    }


def test_fetch_states_omits_bounds_when_absent():
    provider = OpenSkyProvider()
    provider._client = _Client()

    asyncio.run(provider.fetch_states(None))

    assert provider._client.last_params == {}


def test_parse_state_maps_fields():
    provider = OpenSkyProvider()
    row = [
        "39de57",
        "TVF431J ",
        "France",
        1690000000,
        1690000001,
        10.928,
        54.2975,
        11582.4,
        False,
        230.1,
        218.89,
        0.0,
        None,
        11600.0,
        "1000",
        False,
        0,
    ]

    state = provider._parse_state(row)
    assert state is not None
    assert state.icao24 == "39de57"
    assert state.callsign == "TVF431J"  # trailing space trimmed
    assert state.latitude == 54.2975
    assert state.longitude == 10.928
    assert state.altitude_m == 11582.4
    assert state.on_ground is False


def test_parse_state_rejects_bad_icao():
    provider = OpenSkyProvider()
    row = ["zzz", "X", "US", None, 1, 1.0, 1.0, None, False, None, None, None, None, None, None, False, 0]
    assert provider._parse_state(row) is None


def test_parse_state_handles_missing_position():
    provider = OpenSkyProvider()
    row = [
        "abc123",
        "TEST",
        "US",
        None,
        1690000001,
        None,
        None,
        None,
        True,
        None,
        None,
        None,
        None,
        None,
        None,
        False,
        0,
    ]
    state = provider._parse_state(row)
    assert state is not None
    assert state.latitude is None
    assert state.longitude is None
