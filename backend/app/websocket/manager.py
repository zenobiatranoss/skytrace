import asyncio

from fastapi import WebSocket

from app.core.logging import get_logger

log = get_logger(__name__)


class ConnectionManager:
    """tracks the open websocket clients and fans messages out to them.

    sends are guarded with a lock-free copy so a slow client that dies
    mid-send doesn't stop the others."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        log.debug("client connected, %d total", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        log.debug("client disconnected, %d left", len(self._connections))

    @property
    def count(self) -> int:
        return len(self._connections)

    async def broadcast(self, message: dict) -> None:
        if not self._connections:
            return

        dead: list[WebSocket] = []
        for websocket in list(self._connections):
            try:
                await websocket.send_json(message)
            except Exception:  # noqa: BLE001 - a dead socket shouldn't kill the broadcast
                dead.append(websocket)

        for websocket in dead:
            await self.disconnect(websocket)


manager = ConnectionManager()
