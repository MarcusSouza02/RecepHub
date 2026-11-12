from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "recephub"
    postgres_user: str = "recephub"
    postgres_password: str = ""
    auth_origin: str = "http://localhost:3000"
    auth_secure_cookie: bool = False
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, values: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        for value in values:
            parsed = urlsplit(value)
            if (
                value == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
            ):
                raise ValueError("CORS exige origens HTTP explícitas, sem caminho ou credenciais")
        return values

    @property
    def session_cookie_name(self) -> str:
        return "__Host-recephub_session" if self.auth_secure_cookie else "recephub_session"

    @model_validator(mode="after")
    def validate_auth(self):
        self.explicit_origins([self.auth_origin])
        if self.environment == "production" and (
            not self.auth_secure_cookie or not self.auth_origin.startswith("https://")
        ):
            raise ValueError("Produção exige AUTH_ORIGIN HTTPS e AUTH_SECURE_COOKIE=true")
        if self.auth_secure_cookie and not self.auth_origin.startswith("https://"):
            raise ValueError("Cookie seguro exige origem HTTPS")
        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
