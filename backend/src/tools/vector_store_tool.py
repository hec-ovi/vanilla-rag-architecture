"""Vector store abstraction supporting FAISS and Chroma."""

import os
import uuid
from pathlib import Path
from typing import Protocol

import structlog

from src.core import Settings, VectorStoreError

logger = structlog.get_logger()


class VectorStore(Protocol):
    """Protocol defining vector store interface."""

    def add(self, texts: list[str], embeddings: list[list[float]], metadata: list[dict]) -> list[str]: ...
    def search(self, query_embedding: list[float], top_k: int) -> list[dict]: ...
    def delete_all(self) -> None: ...
    def save(self) -> None: ...


class FaissVectorStore:
    """FAISS-based vector store (CPU-optimized, in-memory)."""

    def __init__(self, dimension: int, index_path: str | None = None):
        """Initialize FAISS store.

        Args:
            dimension: Embedding dimension.
            index_path: Optional path to persist index.
        """
        self._dimension = dimension
        self._index_path = index_path
        self._texts: list[str] = []
        self._metadata: list[dict] = []
        self._ids: list[str] = []

        # Import faiss here to avoid dependency if not used
        try:
            import faiss
            self._faiss = faiss
            self._index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
            logger.info("faiss_store_initialized", dimension=dimension)
        except ImportError as e:
            raise VectorStoreError(f"FAISS not installed: {e}") from e

        # Load existing index if available
        if index_path and Path(index_path).exists():
            self._load()

    def _load(self) -> None:
        """Load index from disk."""
        if not self._index_path:
            return

        try:
            import pickle

            index_file = Path(self._index_path) / "faiss.index"
            data_file = Path(self._index_path) / "data.pkl"

            if index_file.exists() and data_file.exists():
                self._index = self._faiss.read_index(str(index_file))
                with open(data_file, "rb") as f:
                    data = pickle.load(f)
                    self._texts = data["texts"]
                    self._metadata = data["metadata"]
                    self._ids = data["ids"]
                logger.info("faiss_index_loaded", doc_count=len(self._ids))
        except Exception as e:
            logger.error("faiss_load_failed", error=str(e))
            # Continue with empty index

    def _save(self) -> None:
        """Save index to disk."""
        if not self._index_path:
            return

        try:
            import pickle

            Path(self._index_path).mkdir(parents=True, exist_ok=True)

            index_file = Path(self._index_path) / "faiss.index"
            data_file = Path(self._index_path) / "data.pkl"

            self._faiss.write_index(self._index, str(index_file))
            with open(data_file, "wb") as f:
                pickle.dump({
                    "texts": self._texts,
                    "metadata": self._metadata,
                    "ids": self._ids,
                }, f)

            logger.debug("faiss_index_saved", doc_count=len(self._ids))
        except Exception as e:
            logger.error("faiss_save_failed", error=str(e))
            raise VectorStoreError(f"Failed to save FAISS index: {e}") from e

    def add(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict],
    ) -> list[str]:
        """Add documents to the store."""
        if not texts:
            return []

        # Generate IDs
        ids = [str(uuid.uuid4()) for _ in texts]

        # Normalize embeddings for cosine similarity
        import numpy as np
        embeddings_array = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized = embeddings_array / norms

        # Add to FAISS index
        self._index.add(normalized)

        # Store texts and metadata
        self._texts.extend(texts)
        self._metadata.extend(metadata)
        self._ids.extend(ids)

        self._save()

        logger.debug("faiss_documents_added", count=len(ids))
        return ids

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        """Search for similar documents."""
        if self._index.ntotal == 0:
            return []

        import numpy as np

        # Normalize query embedding
        query_array = np.array([query_embedding], dtype=np.float32)
        norm = np.linalg.norm(query_array)
        if norm > 0:
            query_array = query_array / norm

        # Search
        scores, indices = self._index.search(query_array, min(top_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._texts):
                results.append({
                    "id": self._ids[idx],
                    "text": self._texts[idx],
                    "metadata": self._metadata[idx],
                    "score": float(score),
                })

        return results

    def delete_all(self) -> None:
        """Delete all documents."""
        self._index = self._faiss.IndexFlatIP(self._dimension)
        self._texts = []
        self._metadata = []
        self._ids = []
        self._save()
        logger.info("faiss_index_cleared")

    def save(self) -> None:
        """Explicit save call."""
        self._save()


class ChromaVectorStore:
    """ChromaDB-based vector store (persistent, easy scaling)."""

    def __init__(self, collection_name: str, persist_path: str):
        """Initialize Chroma store.

        Args:
            collection_name: Name of the collection.
            persist_path: Path for persistence.
        """
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.Client(
                ChromaSettings(
                    persist_directory=persist_path,
                    is_persistent=True,
                )
            )
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("chroma_store_initialized", collection=collection_name)
        except ImportError as e:
            raise VectorStoreError(f"ChromaDB not installed: {e}") from e

    def add(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict],
    ) -> list[str]:
        """Add documents to the store."""
        if not texts:
            return []

        ids = [str(uuid.uuid4()) for _ in texts]

        # Chroma expects metadata to be serializable
        clean_metadata = []
        for meta in metadata:
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            clean_metadata.append(clean_meta)

        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=clean_metadata,
        )

        logger.debug("chroma_documents_added", count=len(ids))
        return ids

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        """Search for similar documents."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i, doc_id in enumerate(results["ids"][0]):
            # Chroma returns cosine distance, convert to similarity
            distance = results["distances"][0][i]
            similarity = 1.0 - distance

            output.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": similarity,
            })

        return output

    def delete_all(self) -> None:
        """Delete all documents."""
        # Get all IDs and delete them
        all_data = self._collection.get()
        if all_data["ids"]:
            self._collection.delete(ids=all_data["ids"])
        logger.info("chroma_collection_cleared")

    def save(self) -> None:
        """Explicit save (Chroma persists automatically)."""
        pass


class VectorStoreTool:
    """Tool for managing vector store operations with configurable backend."""

    def __init__(self, settings: Settings | None = None):
        """Initialize vector store tool.

        Args:
            settings: Application settings.
        """
        self._settings = settings or Settings()
        self._store: VectorStore | None = None
        self._dimension: int | None = None

    def initialize(self, dimension: int) -> None:
        """Initialize the underlying vector store.

        Args:
            dimension: Embedding dimension.
        """
        self._dimension = dimension

        store_type = self._settings.vector_db_type
        persist_path = self._settings.vector_db_path

        if store_type == "faiss":
            self._store = FaissVectorStore(dimension, persist_path)
        elif store_type == "chroma":
            self._store = ChromaVectorStore("documents", persist_path)
        else:
            raise VectorStoreError(f"Unknown vector store type: {store_type}")

        logger.info("vector_store_initialized", type=store_type, dimension=dimension)

    def ensure_initialized(self) -> VectorStore:
        """Ensure store is initialized and return it."""
        if self._store is None:
            raise VectorStoreError("Vector store not initialized. Call initialize() first.")
        return self._store

    async def add(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict],
    ) -> list[str]:
        """Add documents to the vector store."""
        store = self.ensure_initialized()
        return store.add(texts, embeddings, metadata)

    async def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        """Search for similar documents."""
        store = self.ensure_initialized()
        return store.search(query_embedding, top_k)

    async def delete_all(self) -> None:
        """Delete all documents from the store."""
        store = self.ensure_initialized()
        store.delete_all()

    async def save(self) -> None:
        """Explicitly save the store."""
        store = self.ensure_initialized()
        store.save()
