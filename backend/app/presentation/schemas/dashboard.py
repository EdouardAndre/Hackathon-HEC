from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class DashboardSupplierOption(BaseModel):
    supplier_name: str
    unit_price: float
    lead_time_days: int
    reliability_score: float
    available_quantity: int


class DashboardItem(BaseModel):
    id: str
    name: str
    sku: str
    store_id: int
    item_id: int
    current_quantity: int
    reorder_point: int
    status: str
    expected_shortage_date: date | None
    required_quantity: int
    forecast_source: str
    best_option: DashboardSupplierOption
    alternatives: list[DashboardSupplierOption]


class DashboardItemsResponse(BaseModel):
    items: list[DashboardItem]
