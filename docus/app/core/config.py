from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_KEYS = {"change_me_to_a_long_random_secret", ""}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "RA Nutrition and Lifestyle API"
    environment: str = Field(alias="ENVIRONMENT")
    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(alias="REFRESH_TOKEN_EXPIRE_DAYS")
    usda_api_key: str = Field(alias="USDA_API_KEY")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "ra-app"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"], alias="CORS_ORIGINS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def cookie_secure(self) -> bool:
        return self.environment != "development"

    @model_validator(mode="after")
    def _check_secret_key(self) -> "Settings":
        if self.environment != "development":
            if self.secret_key in _PLACEHOLDER_KEYS or len(self.secret_key) < 32:
                raise RuntimeError(
                    "SECRET_KEY is insecure for non-development environment. "
                    "Set a random key of at least 32 characters."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
