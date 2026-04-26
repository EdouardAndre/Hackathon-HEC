from __future__ import annotations

import math
from dataclasses import dataclass

from app.presentation.schemas.dashboard import (
    DashboardItem,
    DashboardItemsResponse,
    DashboardSupplierOption,
)
from app.presentation.schemas.forecasting import ForecastRequest
from app.services.forecasting import ForecastingService


@dataclass(frozen=True)
class DashboardScenario:
    store_id: int
    item_id: int
    current_stock: int


SUPPLIER_OPTIONS: tuple[DashboardSupplierOption, ...] = (
    DashboardSupplierOption(
        supplier_name="Nova Supply",
        unit_price=14.20,
        lead_time_days=4,
        reliability_score=0.97,
        available_quantity=900,
    ),
    DashboardSupplierOption(
        supplier_name="Atlas Wholesale",
        unit_price=13.90,
        lead_time_days=7,
        reliability_score=0.89,
        available_quantity=1200,
    ),
    DashboardSupplierOption(
        supplier_name="BlueRiver Trading",
        unit_price=14.80,
        lead_time_days=3,
        reliability_score=0.94,
        available_quantity=650,
    ),
)

DEFAULT_SCENARIOS: tuple[DashboardScenario, ...] = (
    DashboardScenario(store_id=1, item_id=1, current_stock=80),
    DashboardScenario(store_id=2, item_id=9, current_stock=120),
    DashboardScenario(store_id=3, item_id=7, current_stock=500),
    DashboardScenario(store_id=5, item_id=15, current_stock=200),
)


class DashboardService:
    def __init__(self, forecasting_service: ForecastingService) -> None:
        self.forecasting_service = forecasting_service

    def list_items(self) -> DashboardItemsResponse:
        items = [self._build_item(scenario) for scenario in DEFAULT_SCENARIOS]
        items.sort(key=lambda item: (self._status_rank(item.status), item.current_quantity))
        return DashboardItemsResponse(items=items)

    def _build_item(self, scenario: DashboardScenario) -> DashboardItem:
        forecast = self.forecasting_service.generate_forecast(
            ForecastRequest(
                store_id=scenario.store_id,
                item_id=scenario.item_id,
                current_stock=scenario.current_stock,
                prediction_days=14,
            )
        )
        median_demand = sum(day.quantity_median for day in forecast.daily_forecasts[:7])
        reorder_point = max(1, math.ceil(median_demand))
        status = self._derive_status(forecast.required_quantity, forecast.expected_shortage_date)

        return DashboardItem(
            id=f"store-{scenario.store_id}-item-{scenario.item_id}",
            name=f"Item {scenario.item_id}",
            sku=f"ST{scenario.store_id:02d}-IT{scenario.item_id:02d}",
            store_id=scenario.store_id,
            item_id=scenario.item_id,
            current_quantity=scenario.current_stock,
            reorder_point=reorder_point,
            status=status,
            expected_shortage_date=forecast.expected_shortage_date,
            required_quantity=forecast.required_quantity,
            forecast_source=forecast.source,
            best_option=SUPPLIER_OPTIONS[0],
            alternatives=list(SUPPLIER_OPTIONS[1:]),
        )

    def _derive_status(self, required_quantity: int, shortage_date: object) -> str:
        if shortage_date is not None and required_quantity > 0:
            return "critical"
        if required_quantity > 0:
            return "warning"
        return "healthy"

    def _status_rank(self, status: str) -> int:
        return {"critical": 0, "warning": 1, "healthy": 2}[status]
