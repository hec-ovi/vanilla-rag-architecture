"""SentenceTransformer embedding tool."""

import structlog
from sentence_transformers import SentenceTransformer

from src.core import EmbeddingError, Settings

logger = structlog.get_logger()


class EmbeddingTool:
    """Tool for generating text embeddings using SentenceTransformers."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the embedding model.

        Args:
            settings: Application settings. Uses default if not provided.
        """
        self._settings = settings or Settings()
        self._model: SentenceTransformer | None = None
        self._dimension: int | None = None

    def _load_model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            try:
                logger.info(
                    "loading_embedding_model",
                    model=self._settings.embedding_model,
                    device=self._settings.embedding_device,
                )
                self._model = SentenceTransformer(
                    self._settings.embedding_model,
                    device=self._settings.embedding_device,
                )
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(
                    "embedding_model_loaded",
                    dimension=self._dimension,
                )
            except Exception as e:
                logger.error("embedding_model_load_failed", error=str(e))
                raise EmbeddingError(f"Failed to load embedding model: {e}") from e
        return self._model

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            _ = self._load_model()
        return self._dimension or 384  # Default for all-MiniLM-L6-v2

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not texts:
            return []

        model = self._load_model()

        try:
            embeddings = model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error("embedding_failed", error=str(e), text_count=len(texts))
            raise EmbeddingError(f"Failed to generate embeddings: {e}") from e

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text.

        Args:
            text: Query text to embed.

        Returns:
            Embedding vector.
        """
        embeddings = await self.embed([text])
        return embeddings[0] if embeddings else []
