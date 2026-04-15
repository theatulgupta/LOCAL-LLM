"""Configuration management for the application"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import logging


class Settings(BaseSettings):
    """Application configuration settings"""

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Local LLM Server"
    api_version: str = "1.0.0"
    debug: bool = False

    # Ollama Settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_timeout: int = 300  # 5 minutes

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window_seconds: int = 60  # time window

    # Validation
    max_prompt_length: int = 4096
    max_response_length: int = 8192

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/server.log"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cache and return settings instance"""
    return Settings()


def setup_logging():
    """Configure logging for the application"""
    settings = get_settings()

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )
