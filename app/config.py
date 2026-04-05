import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    llm_model: str = "gpt-4o-mini"

    langchain_tracing_v2: bool = True
    langsmith_api_key: str = ""
    langchain_project: str = "fraud-monitor-agents"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    host: str = "0.0.0.0"
    port: int = 8001
    api_key: str = ""

    agent_timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_agent_retries: int = Field(default=2, ge=0, le=10)
    rate_limit_monitor_per_minute: int = Field(default=20, ge=0, le=10000)
    rate_limit_agent_invoke_per_minute: int = Field(default=30, ge=0, le=10000)

    fraud_patterns_path: str = "data/fraud_patterns.json"
    cors_allow_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:8501,"
        "http://127.0.0.1:8501"
    )

    def apply_langsmith_env(self) -> None:
        tracing_enabled = self.langchain_tracing_v2 and bool(self.langsmith_api_key)
        os.environ["LANGCHAIN_TRACING_V2"] = "true" if tracing_enabled else "false"
        os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = self.langchain_endpoint

    def parsed_cors_allow_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
        return origins or ["http://localhost:3000"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
