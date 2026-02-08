"""Cross-encoder reranker tool for semantic reranking."""

import structlog
from sentence_transformers import CrossEncoder

from src.core import RerankerError, Settings

logger = structlog.get_logger()


class RerankerTool:
    """Tool for reranking documents using cross-encoder models."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the reranker model.

        Args:
            settings: Application settings. Uses default if not provided.
        """
        self._settings = settings or Settings()
        self._model: CrossEncoder | None = None

    def _load_model(self) -> CrossEncoder:
        """Lazy-load the reranker model."""
        if self._model is None:
            try:
                logger.info(
                    "loading_reranker_model",
                    model=self._settings.reranker_model,
                )
                self._model = CrossEncoder(self._settings.reranker_model)
                logger.info("reranker_model_loaded")
            except Exception as e:
                logger.error("reranker_model_load_failed", error=str(e))
                raise RerankerError(f"Failed to load reranker model: {e}") from e
        return self._model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None,
    ) -> list[tuple[int, float]]:
        """Rerank documents based on relevance to query.

        Args:
            query: The search query.
            documents: List of document texts to rerank.
            top_k: Number of top documents to return. Uses settings default if None.

        Returns:
            List of (index, score) tuples sorted by relevance (highest first).

        Raises:
            RerankerError: If reranking fails.
        """
        if not documents:
            return []

        if top_k is None:
            top_k = self._settings.top_k_rerank

        model = self._load_model()

        try:
            # Create query-document pairs
            pairs = [(query, doc) for doc in documents]

            # Get relevance scores
            scores = model.predict(pairs)

            # Create (index, score) tuples and sort by score descending
            indexed_scores = list(enumerate(scores))
            indexed_scores.sort(key=lambda x: x[1], reverse=True)

            # Return top_k results
            return indexed_scores[:top_k]

        except Exception as e:
            logger.error("reranking_failed", error=str(e), doc_count=len(documents))
            raise RerankerError(f"Failed to rerank documents: {e}") from e
