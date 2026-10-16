from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    detail: str


class DataStatus(BaseModel):
    """how trustworthy a piece of info currently is"""

    last_updated: datetime | None = None
    age_seconds: float | None = None
    is_stale: bool = False
