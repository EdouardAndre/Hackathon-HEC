from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventorySnapshotCreate(BaseModel):
    stock_level: int = Field(ge=0)


class InventorySnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_level: int
    recorded_at: datetime
