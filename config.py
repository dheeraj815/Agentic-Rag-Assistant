"""
config.py
Centralized configuration management using Pydantic Settings.
Loads all environment variables from .env and exposes a singleton `settings` object.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide configuration.
    All values can be overridden via environment variables or a `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== LLM API Keys =====
    GROQ_API_KEY: str = Field(default="", description="Groq API key (primary LLM)")
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None, description="Anthropic API key (optional verification)"
    )

    # ===== Web Search =====
    TAVILY_API_KEY: str = Field(default="", description="Tavily search API key")

    # ===== Model Configuration =====
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    GROQ_TEMPERATURE: float = Field(default=0.1)

    # ===== Embeddings =====
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")

    # ===== Vector Store =====
    CHROMA_PERSIST_DIR: str = Field(default="./chroma_db")
    CHROMA_COLLECTION_NAME: str = Field(default="rag_documents")

    # ===== Database =====
    SQLITE_DB_PATH: str = Field(default="./database/app.db")

    # ===== Retrieval =====
    TOP_K_RESULTS: int = Field(default=5)
    CHUNK_SIZE: int = Field(default=1000)
    CHUNK_OVERLAP: int = Field(default=200)

    # ===== Confidence Thresholds =====
    HALLUCINATION_THRESHOLD: float = Field(default=0.6)
    CONFIDENCE_THRESHOLD: float = Field(default=0.5)

    # ===== Reports =====
    REPORTS_DIR: str = Field(default="./reports")

    # ===== Logging =====
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="./logs/app.log")

    @property
    def base_dir(self) -> Path:
        """Project root directory (where this config.py lives)."""
        return Path(__file__).resolve().parent

    def ensure_directories(self) -> None:
        """Create all required runtime directories if they don't exist."""
        dirs = [
            self.base_dir / Path(self.CHROMA_PERSIST_DIR),
            self.base_dir / Path(self.SQLITE_DB_PATH).parent,
            self.base_dir / Path(self.REPORTS_DIR),
            self.base_dir / Path(self.LOG_FILE).parent,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# Singleton settings instance used across the entire application
settings = Settings()
settings.ensure_directories()
