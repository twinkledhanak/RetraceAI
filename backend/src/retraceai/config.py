from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RETRACE_", env_file=".env", extra="ignore")

    app_name: str = "RetraceAI"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    mongodb_uri: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("RETRACE_MONGODB_URI", "MONGODB_URI"),
    )
    gcp_project: str = "project-8a407ddf-d88d-418f-830"
    gcp_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-pro"
    embedding_model: str = "gemini-embedding-001"
    mongo_db: str = "Twinkle_DB"
    mongo_collection: str = "Upgrade_Sessions"
    vector_index_name: str = "autoembed_index"
    vector_path: str = "attempts.errorText"


@lru_cache
def get_settings() -> Settings:
    return Settings()
