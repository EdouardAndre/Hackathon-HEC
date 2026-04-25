from app.api.deps import ForecastingServiceDep
from app.schemas.forecasting import ForecastRequest, ForecastResponse
from app.services.forecasting import ForecastingService
from fastapi import APIRouter

router = APIRouter()


@router.post("/manual", response_model=ForecastResponse)
def submit_manual_forecast(
    payload: ForecastRequest,
    service: ForecastingService = ForecastingServiceDep,
) -> ForecastResponse:
    return service.generate_forecast(payload)
