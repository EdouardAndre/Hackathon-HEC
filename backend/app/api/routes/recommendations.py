from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import DBSession
from app.repositories.suppliers import SupplierRepository
from app.schemas.forecasting import ForecastRequest
from app.schemas.recommendations import SupplierRecommendationResponse
from app.services.supplier_recommendation import SupplierRecommendationService

router = APIRouter()


@router.post("/suppliers", response_model=SupplierRecommendationResponse)
def recommend_suppliers(
    payload: ForecastRequest,
    db: Session = DBSession,
) -> SupplierRecommendationResponse:
    repository = SupplierRepository(db)
    service = SupplierRecommendationService(repository)
    return service.recommend(payload)
