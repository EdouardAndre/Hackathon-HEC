from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.presentation.deps import DBSession, ForecastingServiceDep
from app.presentation.schemas.forecasting import ForecastRequest
from app.presentation.schemas.recommendations import SupplierRecommendationResponse
from app.repositories.suppliers import SupplierRepository
from app.services.forecasting import ForecastingService
from app.services.supplier_recommendation import SupplierRecommendationService

router = APIRouter()


@router.post(
    "/suppliers",
    response_model=SupplierRecommendationResponse,
    summary="Recommander les fournisseurs",
    description=(
        "Exécute une prévision Chronos puis classe tous les fournisseurs enregistrés "
        "selon leur capacité à couvrir la demande prévue. "
        "Le score combine : taux de remplissage (35 %), fiabilité (20 %), prix (20 %), "
        "disponibilité (15 %), délai (10 %)."
    ),
)
def recommend_suppliers(
    payload: ForecastRequest,
    db: Session = DBSession,
    forecasting_service: ForecastingService = ForecastingServiceDep,
) -> SupplierRecommendationResponse:
    try:
        repository = SupplierRepository(db)
        service = SupplierRecommendationService(repository, forecasting_service)
        return service.recommend(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
