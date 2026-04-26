from fastapi import APIRouter, HTTPException

from app.presentation.deps import ForecastingServiceDep
from app.presentation.schemas.forecasting import ForecastRequest, PredictResponse
from app.services.forecasting import ForecastingService

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Prédire la quantité à commander (Chronos T5)",
    description=(
        "Lance une prévision sur `prediction_days` jours pour un article et un magasin donnés. "
        "Retourne uniquement la quantité à commander pour couvrir la demande prévue."
    ),
)
def predict_demand(
    payload: ForecastRequest,
    service: ForecastingService = ForecastingServiceDep,
) -> PredictResponse:
    try:
        forecast = service.generate_forecast(payload)
        return PredictResponse(required_quantity=forecast.required_quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
