from app.cache.aircraft_cache import aircraft_cache
from app.schemas.aircraft import AircraftPosition
from app.services import position_service
from app.websocket.manager import manager

# full-world snapshots get big fast (10k+ aircraft), so the wire format is
# rows of values against a field list instead of objects with repeated keys.
# roughly 4x smaller, and the client rebuilds the same shape from these.
POSITION_FIELDS = [
    "icao24",
    "callsign",
    "latitude",
    "longitude",
    "altitude_m",
    "velocity_ms",
    "heading",
    "vertical_rate_ms",
    "on_ground",
    "status",
    "last_contact",
    "age_seconds",
    "is_stale",
]


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


# the status string repeats 12k times per snapshot, so we ship a number and
# let the client map it back
STATUS_CODES = {"unknown": 0, "on_ground": 1, "airborne": 2, "stale": 3}


def _pack(position: AircraftPosition) -> list:
    last_contact = (
        int(position.last_contact.timestamp()) if position.last_contact else None
    )
    return [
        position.icao24,
        position.callsign,
        _round(position.latitude, 4),
        _round(position.longitude, 4),
        _round(position.altitude_m, 1),
        _round(position.velocity_ms, 1),
        _round(position.heading, 1),
        _round(position.vertical_rate_ms, 2),
        position.on_ground,
        STATUS_CODES.get(position.status, 0),
        last_contact,
        _round(position.age_seconds, 1),
        position.is_stale,
    ]


async def broadcast_positions() -> None:
    """push the current cache to every connected client as one message.
    the ui replaces its aircraft set with this - no per-plane requests."""
    if manager.count == 0:
        return

    positions = position_service.snapshot()
    await manager.broadcast(
        {
            "type": "positions",
            "updated_at": aircraft_cache.updated_at.isoformat()
            if aircraft_cache.updated_at
            else None,
            "count": len(positions),
            "fields": POSITION_FIELDS,
            "aircraft": [_pack(p) for p in positions],
        }
    )


async def send_status(websocket) -> None:
    """small hello so the client knows what it connected to"""
    await websocket.send_json(
        {
            "type": "status",
            "aircraft_tracked": aircraft_cache.size(),
        }
    )


async def broadcast_anomalies(items: list) -> None:
    """push the current set of flagged aircraft. the client keeps its own
    copy and highlights them on the map."""
    if manager.count == 0:
        return

    await manager.broadcast(
        {
            "type": "anomalies",
            "count": len(items),
            "items": [item.model_dump(mode="json") for item in items],
        }
    )
