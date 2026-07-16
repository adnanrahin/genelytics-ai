from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class LLMSettings(BaseModel):
    """LLM connection settings — values come from YAML / env, not code defaults.

    Supported providers (set in config):
      - ollama
      - openai
      - openai_compatible  (Azure, Groq, local gateways, etc.)
      - bedrock            (AWS Bedrock via langchain-aws)
    """

    model_config = {"extra": "allow"}

    provider: str
    model: str
    temperature: float
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    # AWS Bedrock (and similar cloud providers)
    region: Optional[str] = None
    region_name: Optional[str] = None  # alias accepted from YAML
    model_id: Optional[str] = None  # Bedrock model id; falls back to `model`
    credentials_profile_name: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    provider_stop_sequences: Optional[list[str]] = None
    max_tokens: Optional[int] = None

    # Escape hatch for provider-specific kwargs forwarded to the chat client
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return (value or "").strip().lower()

    def resolved_region(self) -> Optional[str]:
        return self.region_name or self.region

    def resolved_model_id(self) -> str:
        return self.model_id or self.model


class DatabaseSettings(BaseModel):
    model_config = {"extra": "allow"}

    uri: Optional[str] = None


class AnalyticsSettings(BaseModel):
    model_config = {"extra": "allow"}

    max_rows: int
    query_timeout_seconds: int
    read_only: bool


class FewShotSettings(BaseModel):
    model_config = {"extra": "allow"}

    path: str
    enabled: bool
    max_examples: int


class Settings(BaseModel):
    """Runtime settings loaded from config/environments/{env}.yaml (+ env overrides).

    Nothing provider-specific is hard-coded here — pick an env with GENELYTICS_ENV
    and put values in the matching YAML file.
    """

    model_config = {"extra": "allow"}

    env: str
    llm: LLMSettings
    database: DatabaseSettings
    analytics: AnalyticsSettings
    few_shot: FewShotSettings
