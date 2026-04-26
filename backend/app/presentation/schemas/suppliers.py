from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupplierBase(BaseModel):
    lead_time_days: int = Field(ge=0)
    available_quantity: int = Field(ge=0)
    current_unit_price: float = Field(gt=0)
    reliability_score: float = Field(ge=0, le=1)


class SupplierCreate(SupplierBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Fournisseur fiable, livraison rapide",
                    "value": {
                        "lead_time_days": 3,
                        "available_quantity": 800,
                        "current_unit_price": 11.50,
                        "reliability_score": 0.95,
                    },
                },
                {
                    "summary": "Fournisseur économique, délai plus long",
                    "value": {
                        "lead_time_days": 7,
                        "available_quantity": 1200,
                        "current_unit_price": 8.20,
                        "reliability_score": 0.78,
                    },
                },
            ]
        }
    )


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
