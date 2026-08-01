from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # AI Provider
    openai_api_key: str = ""
    ai_model: str = "gpt-4o"           # or "ollama/llama3"
    ollama_base_url: str = "http://localhost:11434"

    # GitHub
    github_token: str = ""

    # Semgrep
    semgrep_timeout: int = 60
    semgrep_config: str = "auto"        # semgrep ruleset: "auto", "p/python", etc.

    # Upload limits
    max_upload_size_mb: int = 10

    # Paths
    uploads_dir: str = "uploads"
    reports_dir: str = "reports"
    templates_dir: str = "backend/templates"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
