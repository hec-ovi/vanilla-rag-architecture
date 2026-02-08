"""Text chunking tool using RecursiveCharacterTextSplitter."""

import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core import Settings

logger = structlog.get_logger()


class TextSplitterTool:
    """Tool for splitting text into chunks using recursive character splitting."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the text splitter.

        Args:
            settings: Application settings. Uses default if not provided.
        """
        self._settings = settings or Settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        logger.debug(
            "text_splitter_initialized",
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )

    def split(self, text: str, metadata: dict | None = None) -> list[dict]:
        """Split text into chunks with metadata.

        Args:
            text: The text to split.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            List of chunk dictionaries with content and metadata.
        """
        if not text or not text.strip():
            return []

        # Use LangChain's splitter
        chunks = self._splitter.create_documents(
            texts=[text],
            metadatas=[metadata or {}],
        )

        # Convert to our format
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "content": chunk.page_content,
                "metadata": {
                    **chunk.metadata,
                    "chunk_index": i,
                    "chunk_total": len(chunks),
                },
            })

        logger.debug(
            "text_split_complete",
            input_length=len(text),
            chunk_count=len(result),
        )

        return result

    def split_batch(self, texts: list[str], metadatas: list[dict] | None = None) -> list[list[dict]]:
        """Split multiple texts into chunks.

        Args:
            texts: List of texts to split.
            metadatas: Optional list of metadata dicts (same length as texts).

        Returns:
            List of chunk lists (one per input text).
        """
        if not texts:
            return []

        metadatas = metadatas or [{} for _ in texts]
        if len(metadatas) != len(texts):
            raise ValueError("metadatas must have same length as texts")

        results = []
        for text, meta in zip(texts, metadatas):
            results.append(self.split(text, meta))

        return results
