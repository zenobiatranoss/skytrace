import asyncio

from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import Bounds, FlightDataProvider
from app.providers.merge import merge_states
from app.schemas.aircraft import StateVector

log = get_logger(__name__)


class MultiSourceProvider(FlightDataProvider):
    """fans one fetch out across several feeds and merges the answers.

    the point is resilience: if one source is rate limited or down the others
    still carry the data. we only give up when every source fails, and when
    that happens the error bubbles up so the refresh loop can flag it."""

    name = "multi"

    def __init__(self, providers: list[FlightDataProvider]) -> None:
        self.providers = list(providers)

    @property
    def source_names(self) -> list[str]:
        return [p.name for p in self.providers]

    async def fetch_states(self, bounds: Bounds | None = None) -> list[StateVector]:
        results = await asyncio.gather(
            *(p.fetch_states(bounds) for p in self.providers),
            return_exceptions=True,
        )

        good: list[list[StateVector]] = []
        failures: list[str] = []
        for provider, result in zip(self.providers, results, strict=True):
            if isinstance(result, Exception):
                failures.append(f"{provider.name}: {result}")
                log.warning("position source %s failed: %s", provider.name, result)
                continue
            good.append(result)

        if not good:
            raise ProviderError(self.name, "all sources failed - " + "; ".join(failures))

        return merge_states(good)

    async def close(self) -> None:
        for provider in self.providers:
            await provider.close()
