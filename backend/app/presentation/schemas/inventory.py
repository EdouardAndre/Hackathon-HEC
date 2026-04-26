from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventorySnapshotCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"summary": "Stock bas", "value": {"stock_level": 80}},
                {"summary": "Stock normal", "value": {"stock_level": 350}},
            ]
        }
    )

    stock_level: int = Field(ge=0, description="Niveau de stock actuel en unités")


class InventorySnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_level: int
    recorded_at: datetime
