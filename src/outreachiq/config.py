from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Deliberately cwd-based, not derived from __file__: this package is installed
# non-editably in Docker (site-packages), where __file__-relative parents would
# resolve outside the project entirely. Every entry point (main.py, scripts/*,
# ui/app.py, the Docker WORKDIR) is run from the project root, so cwd is reliable.
PROJECT_ROOT = Path.cwd()


class Thresholds(BaseModel):
    confidence_floor: float = 0.6
    max_call_wait_seconds: int = 300
    call_poll_interval_seconds: int = 10
    no_pickup_after_seconds: int = 60
    days_back_default: int = 30


def _load_thresholds() -> Thresholds:
    path = PROJECT_ROOT / "config" / "settings.yaml"
    if not path.exists():
        return Thresholds()
    raw = yaml.safe_load(path.read_text()) or {}
    return Thresholds(**raw.get("thresholds", {}))


class Settings(BaseSettings):
    """All secrets and environment-dependent knobs. Never hardcode these in agent code."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"

    voice_provider: Literal["mock", "elevenlabs"] = "mock"
    email_provider: Literal["mock", "gmail"] = "mock"

    elevenlabs_api_key: str | None = None
    elevenlabs_agent_id: str | None = None
    elevenlabs_phone_number_id: str | None = None

    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"
    sender_email: str = "outreach@outreachiq.example.com"

    default_country_code: str = "+1"
    database_url: str = "sqlite:///./outreachiq.sqlite"

    mock_call_outcome: Literal["completed", "failed", "did_not_pick"] | None = None

    thresholds: Thresholds = Field(default_factory=_load_thresholds)


settings = Settings()
