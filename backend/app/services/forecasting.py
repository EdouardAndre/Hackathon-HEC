from __future__ import annotations

from typing import Protocol

from app.schemas.forecasting import ForecastRequest, ForecastResponse


class ForecastingService(Protocol):
    def generate_forecast(self, payload: ForecastRequest) -> ForecastResponse:
        raise NotImplementedError


class ManualForecastingService:
    def generate_forecast(self, payload: ForecastRequest) -> ForecastResponse:
        # TODO: replace this manual adapter with a real ML forecasting integration.
        return ForecastResponse(
            expected_shortage_date=payload.expected_shortage_date,
            required_quantity=payload.required_quantity,
            source="manual",
        )
