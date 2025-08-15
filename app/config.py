from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import certifi


class Settings(BaseSettings):
    """Application settings loaded from environment variables and defaults."""

    # LLMs
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str | None = None
    
    # OpenRouter (alternative LLM provider)
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str | None = None

    # LlamaParse
    LLAMAPARSE_API_KEY: str | None = None

    # Pinecone (cloud-first)
    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX_NAME: str | None = None
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"

    # Embeddings
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Chunking
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 150

    # Data directories
    DATA_DIR: str = "data"
    DOCLING_JSON_DIR: str = "data/docling_json"
    LANGEXT_JSON_DIR: str = "data/langext_json"
    LANGEXT_HTML_DIR: str = "data/langext_html"
    # Docling models directory retained for backward compatibility but not used when LLAMAPARSE is enabled
    DOCLING_MODELS_DIR: str = "data/docling_models"
    # Deprecated Chroma local dir placeholder (no longer used)
    CHROMA_DIR: str = "data/chroma"

    model_config = SettingsConfigDict(
        env_file=(".env", "env.example", ".env.example"),
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Ensure outbound HTTPS libs (urllib3/requests) use certifi CA bundle
    try:
        ca_path = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", ca_path)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_path)
    except Exception:
        pass

    settings = Settings()
    # Ensure directories exist
    for d in (
        settings.DOCLING_JSON_DIR,
        settings.LANGEXT_JSON_DIR,
        settings.LANGEXT_HTML_DIR,
        f"{settings.DATA_DIR}/jds",
    ):
        Path(d).mkdir(parents=True, exist_ok=True)
    return settings


class Health(BaseModel):
    status: str


