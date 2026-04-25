from datetime import date

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    expected_shortage_date: date
    required_quantity: int = Field(gt=0)


class ForecastResponse(ForecastRequest):
    source: str = "manual"
