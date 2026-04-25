from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.integrations.ap2.client import AP2Client, MockAP2Client
from app.services.forecasting import ForecastingService, ManualForecastingService


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_forecasting_service() -> ForecastingService:
    return ManualForecastingService()


def get_ap2_client() -> AP2Client:
    return MockAP2Client()


DBSession = Depends(get_db_session)
ForecastingServiceDep = Depends(get_forecasting_service)
AP2ClientDep = Depends(get_ap2_client)
