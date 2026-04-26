from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.forecasting import ChronosForecastingService, ForecastingService
from app.services.integrations.ap2.client import AP2Client, MockAP2Client


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@lru_cache(maxsize=1)
def get_forecasting_service() -> ForecastingService:
    settings = get_settings()
    return ChronosForecastingService(
        data_path=settings.train_data_path,
        model_name=settings.chronos_model,
    )


def get_ap2_client() -> AP2Client:
    return MockAP2Client()


DBSession = Depends(get_db_session)
ForecastingServiceDep = Depends(get_forecasting_service)
AP2ClientDep = Depends(get_ap2_client)
