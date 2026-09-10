from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    LIVEKIT_API_KEY: str | None = Field(default=None)
    LIVEKIT_API_SECRET: str | None = Field(default=None)
    LIVEKIT_URL: str | None = Field(default=None)

    API_BASE_URL: str = Field(default="http://localhost:8000")


settings = Settings()
