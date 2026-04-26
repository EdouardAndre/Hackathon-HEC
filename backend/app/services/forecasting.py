from __future__ import annotations

import math
from typing import Protocol

import numpy as np
import pandas as pd
import torch
from chronos import ChronosPipeline

from app.presentation.schemas.forecasting import DailyForecast, ForecastRequest, ForecastResponse


class ForecastingService(Protocol):
    def generate_forecast(self, payload: ForecastRequest) -> ForecastResponse:
        raise NotImplementedError


class ChronosForecastingService:
    def __init__(self, data_path: str, model_name: str = "amazon/chronos-t5-small") -> None:
        self._pipeline = ChronosPipeline.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype=torch.float32,
        )
        df = pd.read_csv(data_path)
        df["date"] = pd.to_datetime(df["date"])
        self._df = df

    def generate_forecast(self, payload: ForecastRequest) -> ForecastResponse:
        df = self._df[
            (self._df["store"] == payload.store_id) & (self._df["item"] == payload.item_id)
        ][["date", "sales"]].sort_values("date")

        if df.empty:
            raise ValueError(f"No data found for store={payload.store_id}, item={payload.item_id}")

        history = torch.tensor(df["sales"].values, dtype=torch.float32).unsqueeze(0)
        raw = self._pipeline.predict(
            inputs=history,
            prediction_length=payload.prediction_days,
            num_samples=100,
        )
        low, median, high = np.quantile(raw.numpy(), [0.1, 0.5, 0.9], axis=1)

        future_dates = pd.date_range(
            start=df["date"].iloc[-1] + pd.Timedelta(days=1),
            periods=payload.prediction_days,
        )

        daily_forecasts = [
            DailyForecast(
                date=d.date(),
                quantity_low=max(0.0, float(l)),
                quantity_median=max(0.0, float(m)),
                quantity_high=max(0.0, float(h)),
            )
            for d, l, m, h in zip(future_dates, low[0], median[0], high[0])
        ]

        cumulative = 0.0
        shortage_date = None
        for fc in daily_forecasts:
            cumulative += fc.quantity_median
            if shortage_date is None and cumulative >= payload.current_stock:
                shortage_date = fc.date

        total_demand = sum(fc.quantity_median for fc in daily_forecasts)
        required_quantity = max(0, math.ceil(total_demand - payload.current_stock))

        return ForecastResponse(
            store_id=payload.store_id,
            item_id=payload.item_id,
            expected_shortage_date=shortage_date,
            required_quantity=required_quantity,
            daily_forecasts=daily_forecasts,
            source="chronos",
        )
