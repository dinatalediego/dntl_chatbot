from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "local"
    app_host: str = "127.0.0.1"
    app_port: int = 8080
    database_url: str = "sqlite:///./nido.db"
    medallio_database_url: str = "sqlite:///./medallio.db"
    medallio_schema: str = "raw_cygnus"
    medallio_table: str = "clientes_proyectos"
    medallio_id_column: str = "id"
    medallio_watermark_column: str = "fecha_actualizacion"
    nido_webhook_secret: str = "dev-secret-change-me"
    nido_base_url: str = "http://127.0.0.1:8080"
    message_provider: str = "mock"
    timezone: str = "America/Lima"
    contact_start_hour: int = 8
    contact_end_hour: int = 20
    experiment_control_pct: int = Field(default=0, ge=0, le=100)
    control_outcome_observable: bool = False
    meta_graph_base: str = "https://graph.facebook.com"
    meta_graph_version: str = "vXX.X"
    meta_phone_number_id: str = ""
    meta_access_token: str = ""
    meta_app_secret: str = ""
    meta_verify_token: str = ""
    meta_template_name: str = "hello_world"
    meta_template_language: str = "en_US"


@lru_cache
def get_settings() -> Settings:
    return Settings()
