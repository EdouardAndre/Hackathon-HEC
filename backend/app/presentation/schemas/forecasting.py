from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ForecastRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Stock bas — rupture imminente (Store 1, Item 1)",
                    "value": {
                        "store_id": 1,
                        "item_id": 1,
                        "current_stock": 80,
                        "prediction_days": 7,
                    },
                },
                {
                    "summary": "Stock confortable — horizon 30 jours (Store 3, Item 7)",
                    "value": {
                        "store_id": 3,
                        "item_id": 7,
                        "current_stock": 500,
                        "prediction_days": 30,
                    },
                },
                {
                    "summary": "Article à forte rotation (Store 5, Item 15)",
                    "value": {
                        "store_id": 5,
                        "item_id": 15,
                        "current_stock": 200,
                        "prediction_days": 14,
                    },
                },
            ]
        }
    )

    store_id: int = Field(gt=0, description="Identifiant du magasin (1–10)")
    item_id: int = Field(gt=0, description="Identifiant de l'article (1–50)")
    current_stock: int = Field(gt=0, description="Stock actuel en unités")
    prediction_days: int = Field(
        default=7, gt=0, le=90, description="Nombre de jours à prévoir (max 90)"
    )


class DailyForecast(BaseModel):
    date: date
    quantity_low: float = Field(description="Quantile 10 %")
    quantity_median: float = Field(description="Quantile 50 % — valeur centrale")
    quantity_high: float = Field(description="Quantile 90 %")


class ForecastResponse(BaseModel):
    store_id: int
    item_id: int
    expected_shortage_date: date | None = Field(
        description="Date estimée de rupture de stock (None si le stock tient sur la période)"
    )
    required_quantity: int = Field(
        description="Quantité à commander pour couvrir la demande prévue"
    )
    daily_forecasts: list[DailyForecast]
    source: str = "chronos"


class PredictResponse(BaseModel):
    required_quantity: int = Field(description="Quantité à commander pour couvrir la demande prévue")
