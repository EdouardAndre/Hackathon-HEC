from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hackathon HEC Backend"
    app_env: str = "development"
    database_url: str
    train_data_path: str = "../demand-forecasting-kernels-only/train.csv"
    chronos_model: str = "amazon/chronos-t5-small"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
