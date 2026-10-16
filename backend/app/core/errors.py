from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ProviderError(Exception):
    """raised when an upstream data source misbehaves"""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        self.message = message
        super().__init__(f"{provider}: {message}")


class NotFoundError(Exception):
    def __init__(self, what: str):
        self.what = what
        super().__init__(f"{what} not found")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ProviderError)
    async def _provider(_: Request, exc: ProviderError) -> JSONResponse:
        # upstream trouble isn't the caller's fault
        return JSONResponse(status_code=502, content={"detail": str(exc)})
