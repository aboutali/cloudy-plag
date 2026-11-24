from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "cloudy"
    postgres_password: str = "cloudy"
    postgres_db: str = "cloudy_plag"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    minio_endpoint: str = "minio:9000"
    minio_root_user: str = "cloudy"
    minio_root_password: str = "cloudy-dev-secret"
    minio_bucket: str = "cloudy-plag-documents"
    minio_use_ssl: bool = False

    grobid_url: str | None = None

    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
