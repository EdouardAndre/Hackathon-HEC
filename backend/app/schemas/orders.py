from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.purchase_order import PurchaseOrderStatus


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    quantity: int = Field(gt=0)
    expected_shortage_date: date


class PurchaseOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    quantity: int
    unit_price: float
    status: PurchaseOrderStatus
    expected_shortage_date: date
    ap2_reference: str | None
    created_at: datetime
    updated_at: datetime
