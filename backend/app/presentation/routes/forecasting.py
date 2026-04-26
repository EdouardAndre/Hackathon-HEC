from fastapi import APIRouter, HTTPException

from app.presentation.deps import ForecastingServiceDep
from app.presentation.schemas.forecasting import ForecastRequest, ForecastResponse
from app.services.forecasting import ForecastingService

router = APIRouter()


@router.post(
    "/predict",
    response_model=ForecastResponse,
    summary="Prédire la demande (Chronos T5)",
    description=(
        "Lance une prévision sur `prediction_days` jours pour un article et un magasin donnés. "
        "Retourne les quantités jour par jour (quantiles 10/50/90), la date estimée de rupture "
        "et la quantité à commander."
    ),
)
def predict_demand(
    payload: ForecastRequest,
    service: ForecastingService = ForecastingServiceDep,
) -> ForecastResponse:
    try:
        return service.generate_forecast(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
