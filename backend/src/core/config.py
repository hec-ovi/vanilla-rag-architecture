"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "production", "testing"] = Field(
        default="development",
        description="Application environment",
    )
    log_level: Literal["debug", "info", "warning", "error"] = Field(
        default="info",
        description="Logging level",
    )

    # Server
    backend_host: str = Field(default="0.0.0.0", description="Server bind host")
    backend_port: int = Field(default=8000, description="Server port")

    # Ollama
    ollama_base_url: str = Field(
        default="http://ollama:11434",
        description="Ollama API base URL",
    )
    ollama_model: str = Field(
        default="qwen2.5:14b",
        description="Default LLM model",
    )
    ollama_vision_model: str = Field(
        default="llava:7b",
        description="Vision model for image captioning",
    )
    ollama_context_length: int = Field(
        default=8192,
        description="Context window size in tokens",
    )

    # Vector Database
    vector_db_type: Literal["faiss", "chroma"] = Field(
        default="faiss",
        description="Vector database type",
    )
    vector_db_path: str = Field(
        default="/app/data/vector_db",
        description="Path for vector database storage",
    )

    # Embeddings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
    )
    embedding_device: str = Field(
        default="cpu",
        description="Device for embeddings (cpu/cuda)",
    )

    # Reranker
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model for reranking",
    )

    # Text Chunking
    chunk_size: int = Field(default=500, description="Text chunk size")
    chunk_overlap: int = Field(default=100, description="Text chunk overlap")

    # Retrieval
    top_k_retrieve: int = Field(
        default=10,
        description="Number of documents to retrieve",
    )
    top_k_rerank: int = Field(
        default=3,
        description="Number of documents after reranking",
    )

    # Data paths
    data_dir: str = Field(default="/app/data", description="Data directory")
    uploads_dir: str = Field(default="/app/data/uploads", description="Uploads directory")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
