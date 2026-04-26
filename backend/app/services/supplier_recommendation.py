from __future__ import annotations

from app.repositories.models.supplier import Supplier
from app.repositories.suppliers import SupplierRepository
from app.presentation.schemas.forecasting import ForecastRequest
from app.presentation.schemas.recommendations import (
    SupplierRecommendationItem,
    SupplierRecommendationResponse,
)
from app.services.forecasting import ForecastingService


def rank_suppliers(
    suppliers: list[Supplier],
    required_quantity: int,
) -> list[SupplierRecommendationItem]:
    if not suppliers:
        return []

    max_price = max(float(supplier.current_unit_price) for supplier in suppliers) or 1.0
    max_available = max(supplier.available_quantity for supplier in suppliers) or 1
    max_lead_time = max(supplier.lead_time_days for supplier in suppliers) or 1

    recommendations: list[SupplierRecommendationItem] = []
    for supplier in suppliers:
        can_fulfill = supplier.available_quantity >= required_quantity
        fulfillment_score = 1.0 if can_fulfill else supplier.available_quantity / required_quantity
        price_score = 1 - (float(supplier.current_unit_price) / max_price)
        availability_score = supplier.available_quantity / max_available
        lead_time_score = 1 - (supplier.lead_time_days / max_lead_time)

        score = (
            0.35 * fulfillment_score
            + 0.20 * (supplier.reliability_score or 0.0)
            + 0.20 * price_score
            + 0.15 * availability_score
            + 0.10 * lead_time_score
        )

        recommendations.append(
            SupplierRecommendationItem(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                can_fulfill=can_fulfill,
                recommended_quantity=min(required_quantity, supplier.available_quantity),
                lead_time_days=supplier.lead_time_days,
                available_quantity=supplier.available_quantity,
                current_unit_price=float(supplier.current_unit_price),
                reliability_score=supplier.reliability_score,
                score=round(score, 4),
            )
        )

    return sorted(
        recommendations,
        key=lambda item: (item.can_fulfill, item.score, -item.current_unit_price),
        reverse=True,
    )


class SupplierRecommendationService:
    def __init__(
        self,
        supplier_repository: SupplierRepository,
        forecasting_service: ForecastingService,
    ) -> None:
        self.supplier_repository = supplier_repository
        self.forecasting_service = forecasting_service

    def recommend(self, payload: ForecastRequest) -> SupplierRecommendationResponse:
        forecast = self.forecasting_service.generate_forecast(payload)
        suppliers = self.supplier_repository.list_all()
        recommendations = rank_suppliers(suppliers, forecast.required_quantity)
        return SupplierRecommendationResponse(
            forecast=forecast,
            recommendations=recommendations,
        )
