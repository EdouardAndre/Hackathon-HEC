from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.repositories.models.purchase_order import PurchaseOrderStatus


class PurchaseOrderCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Commande urgente 180 unités",
                    "value": {
                        "supplier_id": 1,
                        "quantity": 180,
                        "expected_shortage_date": "2026-05-03",
                    },
                }
            ]
        }
    )

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
