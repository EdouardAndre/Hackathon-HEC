from pydantic import BaseModel

from app.schemas.forecasting import ForecastResponse


class SupplierRecommendationItem(BaseModel):
    supplier_id: int
    supplier_name: str
    can_fulfill: bool
    recommended_quantity: int
    lead_time_days: int
    available_quantity: int
    current_unit_price: float
    reliability_score: float
    score: float


class SupplierRecommendationResponse(BaseModel):
    forecast: ForecastResponse
    recommendations: list[SupplierRecommendationItem]
