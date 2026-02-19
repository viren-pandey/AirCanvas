from __future__ import annotations

import os
from functools import lru_cache

from pydantic import AliasChoices, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    HAS_PYDANTIC_SETTINGS = True
except ImportError:  # pragma: no cover - offline/local fallback
    BaseSettings = None  # type: ignore[assignment]
    SettingsConfigDict = dict  # type: ignore[assignment]
    HAS_PYDANTIC_SETTINGS = False

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency at runtime
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


def _env_value(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


def _env_bool(*names: str, default: bool = False) -> bool:
    value = _env_value(*names)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(*names: str, default: int) -> int:
    value = _env_value(*names)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


if HAS_PYDANTIC_SETTINGS:

    class Settings(BaseSettings):
        """Backend settings loaded from environment variables and .env."""

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        app_name: str = "AirCanvas Pro API"
        api_prefix: str = "/api/v1"
        debug: bool = False
        environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT"))

        database_url: str = Field(
            default="postgresql+psycopg://postgres:postgres@localhost:5432/aircanvas_pro",
            validation_alias=AliasChoices("DATABASE_URL"),
        )

        jwt_secret: str = Field(
            default="change-me-in-production",
            validation_alias=AliasChoices("JWT_SECRET"),
        )
        jwt_algorithm: str = "HS256"
        jwt_exp_minutes: int = 60 * 24
        admin_bootstrap_secret: str | None = None
        expose_backend_pages: bool = Field(
            default=False,
            validation_alias=AliasChoices("EXPOSE_BACKEND_PAGES"),
        )
        expose_health_endpoints: bool = Field(
            default=False,
            validation_alias=AliasChoices("EXPOSE_HEALTH_ENDPOINTS"),
        )
        expose_api_docs: bool = Field(
            default=False,
            validation_alias=AliasChoices("EXPOSE_API_DOCS"),
        )
        healthcheck_secret: str | None = Field(
            default=None,
            validation_alias=AliasChoices("HEALTHCHECK_SECRET"),
        )

        s3_bucket: str = Field(
            default="aircanvas-pro",
            validation_alias=AliasChoices("S3_BUCKET", "STORAGE_BUCKET"),
        )
        s3_region: str = "us-east-1"
        s3_endpoint_url: str | None = None
        s3_access_key_id: str | None = None
        s3_secret_access_key: str | None = None
        signed_url_ttl_seconds: int = 900

        cors_origins: str = "*"
        cors_allow_credentials: bool = False

        def cors_origin_list(self) -> list[str]:
            if self.cors_origins.strip() == "*":
                return ["*"]
            return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

else:

    class Settings:
        """Fallback settings loader when pydantic-settings is unavailable."""

        def __init__(self) -> None:
            self.app_name = _env_value("APP_NAME", default="AirCanvas Pro API") or "AirCanvas Pro API"
            self.api_prefix = _env_value("API_PREFIX", default="/api/v1") or "/api/v1"
            self.debug = _env_bool("DEBUG", default=False)
            self.environment = _env_value("ENVIRONMENT", default="development") or "development"

            self.database_url = (
                _env_value(
                    "DATABASE_URL",
                    default="postgresql+psycopg://postgres:postgres@localhost:5432/aircanvas_pro",
                )
                or "postgresql+psycopg://postgres:postgres@localhost:5432/aircanvas_pro"
            )

            self.jwt_secret = _env_value("JWT_SECRET", default="change-me-in-production") or "change-me-in-production"
            self.jwt_algorithm = _env_value("JWT_ALGORITHM", default="HS256") or "HS256"
            self.jwt_exp_minutes = _env_int("JWT_EXP_MINUTES", default=60 * 24)
            self.admin_bootstrap_secret = _env_value("ADMIN_BOOTSTRAP_SECRET", default=None)
            self.expose_backend_pages = _env_bool("EXPOSE_BACKEND_PAGES", default=False)
            self.expose_health_endpoints = _env_bool("EXPOSE_HEALTH_ENDPOINTS", default=False)
            self.expose_api_docs = _env_bool("EXPOSE_API_DOCS", default=False)
            self.healthcheck_secret = _env_value("HEALTHCHECK_SECRET", default=None)

            self.s3_bucket = _env_value("S3_BUCKET", "STORAGE_BUCKET", default="aircanvas-pro") or "aircanvas-pro"
            self.s3_region = _env_value("S3_REGION", default="us-east-1") or "us-east-1"
            self.s3_endpoint_url = _env_value("S3_ENDPOINT_URL", default=None)
            self.s3_access_key_id = _env_value("S3_ACCESS_KEY_ID", default=None)
            self.s3_secret_access_key = _env_value("S3_SECRET_ACCESS_KEY", default=None)
            self.signed_url_ttl_seconds = _env_int("SIGNED_URL_TTL_SECONDS", default=900)

            self.cors_origins = _env_value("CORS_ORIGINS", default="*") or "*"
            self.cors_allow_credentials = _env_bool("CORS_ALLOW_CREDENTIALS", default=False)

        def cors_origin_list(self) -> list[str]:
            if self.cors_origins.strip() == "*":
                return ["*"]
            return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
