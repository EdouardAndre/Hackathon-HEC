from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import date

import pandas as pd

from app.presentation.schemas.dashboard import (
    DashboardItem,
    DashboardItemsResponse,
    DashboardSupplierOption,
)
from app.presentation.schemas.forecasting import ForecastRequest
from app.services.forecasting import ForecastingService

_SUPPLIER_DATA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "supplier_dataset.xlsx")
)


@dataclass(frozen=True)
class DashboardItemMetadata:
    item_id: int
    name: str
    sku: str
    unit_label: str
    target_cover_days: int


ITEM_METADATA: tuple[DashboardItemMetadata, ...] = (
    DashboardItemMetadata(
        item_id=1,
        name="Thermal Receipt Paper",
        sku="BOB-POS-ROLL-57",
        unit_label="rolls",
        target_cover_days=4,
    ),
    DashboardItemMetadata(
        item_id=9,
        name="Courier Shipping Pouches",
        sku="BOB-SHP-PCH-001",
        unit_label="packs",
        target_cover_days=7,
    ),
    DashboardItemMetadata(
        item_id=7,
        name="Barcode Label Rolls",
        sku="BOB-LBL-4X6",
        unit_label="rolls",
        target_cover_days=16,
    ),
    DashboardItemMetadata(
        item_id=15,
        name="Tamper-Evident Deposit Bags",
        sku="BOB-DEP-BAG-SEC",
        unit_label="bags",
        target_cover_days=3,
    ),
)


class DashboardService:
    def __init__(self, forecasting_service: ForecastingService, train_data_path: str) -> None:
        self.forecasting_service = forecasting_service
        self._demand_frame = self._load_demand_frame(train_data_path)
        self._supplier_frame = self._load_supplier_frame()

    def list_items(self) -> DashboardItemsResponse:
        items = [
            self._build_item(metadata)
            for metadata in ITEM_METADATA
            if self._has_demand_history(metadata.item_id)
        ]
        items.sort(key=lambda item: (self._status_rank(item.status), item.current_quantity))
        return DashboardItemsResponse(items=items)

    def _build_item(self, metadata: DashboardItemMetadata) -> DashboardItem:
        store_id, current_quantity = self._select_store_context(metadata.item_id)
        forecast = self.forecasting_service.generate_forecast(
            ForecastRequest(
                store_id=store_id,
                item_id=metadata.item_id,
                current_stock=current_quantity,
                prediction_days=14,
            )
        )
        median_demand = sum(day.quantity_median for day in forecast.daily_forecasts[:7])
        reorder_point = max(1, math.ceil(median_demand))
        forecast_start_date = forecast.daily_forecasts[0].date if forecast.daily_forecasts else None
        status = self._derive_status(
            required_quantity=forecast.required_quantity,
            shortage_date=forecast.expected_shortage_date,
            forecast_start_date=forecast_start_date,
        )
        supplier_options = self._select_supplier_options(forecast.required_quantity)
        best_option = supplier_options[0] if supplier_options else None
        alternatives = supplier_options[1:] if len(supplier_options) > 1 else []

        return DashboardItem(
            id=f"store-{store_id}-item-{metadata.item_id}",
            name=metadata.name,
            sku=metadata.sku,
            unit_label=metadata.unit_label,
            store_id=store_id,
            item_id=metadata.item_id,
            current_quantity=current_quantity,
            reorder_point=reorder_point,
            status=status,
            expected_shortage_date=forecast.expected_shortage_date,
            required_quantity=forecast.required_quantity,
            forecast_source=forecast.source,
            best_option=best_option,
            alternatives=alternatives,
        )

    def _select_store_context(self, item_id: int) -> tuple[int, int]:
        item_history = self._demand_frame[self._demand_frame["item"] == item_id].copy()
        if item_history.empty:
            raise ValueError(f"No demand history found for item={item_id}")

        item_history.sort_values(["store", "date"], inplace=True)
        recent_window = item_history.groupby("store").tail(14)
        store_summary = (
            recent_window.groupby("store")["sales"]
            .agg(["sum", "mean"])
            .reset_index()
            .sort_values(["sum", "mean"], ascending=False)
        )

        selected = store_summary.iloc[0]
        store_id = int(selected["store"])
        metadata = next(item for item in ITEM_METADATA if item.item_id == item_id)
        store_history = item_history[item_history["store"] == store_id].sort_values("date")
        recent_mean = float(store_history.tail(7)["sales"].mean())
        current_quantity = max(1, int(math.ceil(recent_mean * metadata.target_cover_days)))
        return store_id, current_quantity

    def _has_demand_history(self, item_id: int) -> bool:
        return bool((self._demand_frame["item"] == item_id).any())

    def _load_demand_frame(self, train_data_path: str) -> pd.DataFrame:
        df = pd.read_csv(train_data_path, usecols=["date", "store", "item", "sales"])
        df["date"] = pd.to_datetime(df["date"])
        return df

    def _load_supplier_frame(self) -> pd.DataFrame:
        return pd.read_excel(_SUPPLIER_DATA_PATH)

    def _select_supplier_options(self, required_quantity: int) -> list[DashboardSupplierOption]:
        ranked = self._supplier_frame.copy()
        ranked["can_fulfill"] = ranked["quantity"] >= required_quantity
        ranked.sort_values(
            ["can_fulfill", "y_score", "reliability", "quantity", "price"],
            ascending=[False, False, False, False, True],
            inplace=True,
        )

        options: list[DashboardSupplierOption] = []
        seen_names: set[str] = set()

        for row in ranked.itertuples(index=False):
            supplier_name = str(row.name)
            if supplier_name in seen_names:
                continue

            options.append(
                DashboardSupplierOption(
                    supplier_name=supplier_name,
                    unit_price=round(float(row.price), 2),
                    lead_time_days=max(1, int(round(float(row.delivery_time)))),
                    reliability_score=round(float(row.reliability), 4),
                    available_quantity=int(row.quantity),
                )
            )
            seen_names.add(supplier_name)

            if len(options) == 3:
                break

        return options

    def _derive_status(
        self,
        required_quantity: int,
        shortage_date: date | None,
        forecast_start_date: date | None,
    ) -> str:
        if shortage_date is not None and forecast_start_date is not None:
            days_until_shortage = (shortage_date - forecast_start_date).days + 1
            if days_until_shortage <= 5:
                return "critical"
        if required_quantity > 0 or shortage_date is not None:
            return "warning"
        return "healthy"

    def _status_rank(self, status: str) -> int:
        return {"critical": 0, "warning": 1, "healthy": 2}[status]
