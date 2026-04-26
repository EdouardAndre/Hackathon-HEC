from fastapi import APIRouter

from app.core.config import get_settings
from app.presentation.deps import ForecastingServiceDep
from app.presentation.schemas.dashboard import DashboardItemsResponse
from app.services.dashboard import DashboardService
from app.services.forecasting import ForecastingService

router = APIRouter()


@router.get(
    "/items",
    response_model=DashboardItemsResponse,
    summary="Lister les articles de démonstration évalués par le modèle",
    description=(
        "Retourne une sélection d'articles issus du dataset de test, enrichis avec "
        "une évaluation Chronos pour alimenter le dashboard frontend."
    ),
)
def list_dashboard_items(
    forecasting_service: ForecastingService = ForecastingServiceDep,
) -> DashboardItemsResponse:
    settings = get_settings()
    service = DashboardService(
        forecasting_service=forecasting_service,
        train_data_path=settings.train_data_path,
    )
    return service.list_items()
