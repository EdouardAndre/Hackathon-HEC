from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    lead_time_days: int = Field(ge=0)
    available_quantity: int = Field(ge=0)
    current_unit_price: float = Field(gt=0)
    reliability_score: float = Field(ge=0, le=1)


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
