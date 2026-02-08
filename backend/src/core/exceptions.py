"""Domain-specific exceptions for the RAG application."""


class RAGError(Exception):
    """Base exception for RAG application."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentProcessingError(RAGError):
    """Raised when document processing fails."""

    pass


class VectorStoreError(RAGError):
    """Raised when vector store operations fail."""

    pass


class EmbeddingError(RAGError):
    """Raised when embedding generation fails."""

    pass


class RerankerError(RAGError):
    """Raised when reranking fails."""

    pass


class LLMError(RAGError):
    """Raised when LLM inference fails."""

    pass


class ConfigurationError(RAGError):
    """Raised when there's a configuration issue."""

    pass
