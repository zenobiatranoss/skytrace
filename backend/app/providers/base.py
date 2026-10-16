from abc import ABC, abstractmethod

from app.schemas.aircraft import StateVector

Bounds = tuple[float, float, float, float]  # lamin, lomin, lamax, lomax


class FlightDataProvider(ABC):
    """contract every position source has to follow. or the point of this:
    swapping providers shouldn't touch the rest of the app."""

    name: str = "base"

    @abstractmethod
    async def fetch_states(self, bounds: Bounds | None = None) -> list[StateVector]:
        """return the current live positions, optionally clipped to a box"""

    async def close(self) -> None:
        """release whatever resource the provider holds"""
        return None
