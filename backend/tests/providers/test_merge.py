import asyncio
from datetime import timedelta

import pytest

from app.core.errors import ProviderError
from app.providers.base import Bounds, FlightDataProvider
from app.providers.merge import merge_states
from app.providers.multi import MultiSourceProvider
from app.schemas.aircraft import StateVector
from app.utils.time import utcnow


def _state(icao24, **kw):
    base = {"icao24": icao24}
    base.update(kw)
    return StateVector(**base)


def test_merge_takes_most_recent_fix_as_base():
    now = utcnow()
    older = _state("abc123", latitude=1.0, last_contact=now - timedelta(seconds=30))
    newer = _state("abc123", latitude=2.0, last_contact=now)

    merged = merge_states([[older], [newer]])

    assert len(merged) == 1
    assert merged[0].latitude == 2.0


def test_merge_fills_missing_fields_from_other_source():
    now = utcnow()
    sparse = _state("abc123", latitude=1.0, longitude=2.0, last_contact=now)
    rich = _state(
        "abc123",
        callsign="TVF431J",
        altitude_m=11000.0,
        squawk="4221",
        last_contact=now - timedelta(seconds=5),
    )

    merged = merge_states([[sparse], [rich]])[0]

    assert merged.latitude == 1.0  # kept from the more recent source
    assert merged.callsign == "TVF431J"
    assert merged.altitude_m == 11000.0
    assert merged.squawk == "4221"


def test_merge_keeps_priority_on_equal_recency():
    now = utcnow()
    high = _state("abc123", callsign="HIGH", last_contact=now)
    low = _state("abc123", callsign="LOW", last_contact=now)

    merged = merge_states([[high], [low]])[0]

    assert merged.callsign == "HIGH"


def test_merge_unions_distinct_aircraft():
    a = _state("aaa111", latitude=1.0)
    b = _state("bbb222", latitude=2.0)

    merged = merge_states([[a], [b]])

    assert {s.icao24 for s in merged} == {"aaa111", "bbb222"}


class _FakeProvider(FlightDataProvider):
    def __init__(self, name, states=None, error=None):
        self.name = name
        self._states = states or []
        self._error = error

    async def fetch_states(self, bounds: Bounds | None = None) -> list[StateVector]:
        if self._error is not None:
            raise self._error
        return self._states


def test_multi_merges_successful_sources():
    now = utcnow()
    primary = _FakeProvider(
        "primary", [_state("abc123", latitude=1.0, last_contact=now)]
    )
    secondary = _FakeProvider(
        "secondary",
        [_state("abc123", altitude_m=9000.0, last_contact=now - timedelta(seconds=1))],
    )

    provider = MultiSourceProvider([primary, secondary])
    states = asyncio.run(provider.fetch_states())

    assert len(states) == 1
    assert states[0].latitude == 1.0
    assert states[0].altitude_m == 9000.0


def test_multi_survives_a_failed_source():
    good = _FakeProvider("good", [_state("abc123", latitude=1.0)])
    bad = _FakeProvider("bad", error=ProviderError("bad", "down"))

    provider = MultiSourceProvider([bad, good])
    states = asyncio.run(provider.fetch_states())

    assert [s.icao24 for s in states] == ["abc123"]


def test_multi_raises_when_all_sources_fail():
    bad1 = _FakeProvider("one", error=ProviderError("one", "down"))
    bad2 = _FakeProvider("two", error=ProviderError("two", "down"))

    provider = MultiSourceProvider([bad1, bad2])

    with pytest.raises(ProviderError):
        asyncio.run(provider.fetch_states())
