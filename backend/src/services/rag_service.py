"""RAG orchestration service."""

import uuid
from pathlib import Path

import structlog

from src.core import RAGError, Settings
from src.models.document import DocumentUpload
from src.models.rag import IngestResponse, QueryRequest, QueryResponse, Source
from src.tools import (
    EmbeddingTool,
    OllamaTool,
    RerankerTool,
    TextSplitterTool,
    VectorStoreTool,
)

from .document_service import DocumentService

logger = structlog.get_logger()


class RAGService:
    """Service for RAG operations: ingest, retrieve, and generate."""

    def __init__(self, settings: Settings | None = None):
        """Initialize RAG service with all required tools.

        Args:
            settings: Application settings.
        """
        self._settings = settings or Settings()
        self._document_service = DocumentService(self._settings)
        self._embedding_tool = EmbeddingTool(self._settings)
        self._reranker_tool = RerankerTool(self._settings)
        self._text_splitter = TextSplitterTool(self._settings)
        self._vector_store = VectorStoreTool(self._settings)
        self._ollama_tool = OllamaTool(self._settings)

        # Track if vector store is initialized
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure vector store is initialized."""
        if not self._initialized:
            dimension = self._embedding_tool.dimension
            self._vector_store.initialize(dimension)
            self._initialized = True
            logger.info("rag_service_initialized", embedding_dim=dimension)

    async def ingest_document(
        self,
        content: bytes,
        filename: str,
    ) -> IngestResponse:
        """Ingest a document into the vector store.

        Args:
            content: Raw document bytes.
            filename: Original filename.

        Returns:
            Ingestion response with chunk count.
        """
        await self._ensure_initialized()

        doc_id = str(uuid.uuid4())

        try:
            # Extract text
            text, doc_type = await self._document_service.extract(content, filename)

            # Split into chunks
            chunks = self._text_splitter.split(
                text,
                metadata={
                    "doc_id": doc_id,
                    "filename": filename,
                    "doc_type": doc_type,
                },
            )

            if not chunks:
                return IngestResponse(
                    doc_id=doc_id,
                    filename=filename,
                    chunk_count=0,
                    status="error",
                    message="No chunks generated from document",
                )

            # Generate embeddings
            texts = [chunk["content"] for chunk in chunks]
            embeddings = await self._embedding_tool.embed(texts)

            # Add to vector store
            metadata = [
                {
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": chunk["metadata"]["chunk_index"],
                    "chunk_total": chunk["metadata"]["chunk_total"],
                }
                for chunk in chunks
            ]

            chunk_ids = await self._vector_store.add(texts, embeddings, metadata)

            logger.info(
                "document_ingested",
                doc_id=doc_id,
                filename=filename,
                chunks=len(chunks),
            )

            return IngestResponse(
                doc_id=doc_id,
                filename=filename,
                chunk_count=len(chunks),
                status="success",
                message=f"Successfully ingested {filename} into {len(chunks)} chunks",
            )

        except Exception as e:
            logger.error("ingestion_failed", filename=filename, error=str(e))
            return IngestResponse(
                doc_id=doc_id,
                filename=filename,
                chunk_count=0,
                status="error",
                message=f"Failed to ingest {filename}: {str(e)}",
            )

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Query the RAG system.

        Args:
            request: Query request with question.

        Returns:
            Query response with answer and sources.
        """
        await self._ensure_initialized()

        logger.info("processing_query", query=request.query)

        # 1. Embed query
        query_embedding = await self._embedding_tool.embed_query(request.query)

        # 2. Retrieve top-K documents from vector store
        retrieve_k = self._settings.top_k_retrieve
        initial_results = await self._vector_store.search(query_embedding, retrieve_k)

        if not initial_results:
            return QueryResponse(
                answer="I don't have enough information to answer this question based on the provided context.",
                sources=[],
                query=request.query,
                model=self._settings.ollama_model,
                tokens_used=None,
            )

        logger.debug("initial_retrieval", count=len(initial_results))

        # 3. Rerank using cross-encoder
        documents = [r["text"] for r in initial_results]
        rerank_k = request.top_k or self._settings.top_k_rerank
        reranked = await self._reranker_tool.rerank(
            request.query,
            documents,
            top_k=rerank_k,
        )

        # 4. Select top reranked documents
        selected_indices = [idx for idx, _ in reranked]
        selected_results = [initial_results[idx] for idx in selected_indices]

        logger.debug("reranking_complete", initial=len(initial_results), final=len(selected_results))

        # 5. Build context from selected documents
        context_parts = []
        for i, result in enumerate(selected_results, 1):
            context_parts.append(f"Document {i}:\n{result['text']}")

        context = "\n\n".join(context_parts)

        # 6. Generate answer using LLM
        try:
            answer = await self._ollama_tool.generate(
                prompt=request.query,
                context=context,
                stream=False,
            )
        except Exception as e:
            logger.error("generation_failed", error=str(e))
            raise RAGError(f"Failed to generate answer: {e}") from e

        # 7. Build sources
        sources = [
            Source(
                chunk_id=result["id"],
                doc_id=result["metadata"].get("doc_id", "unknown"),
                filename=result["metadata"].get("filename", "unknown"),
                content=result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"],
                score=float(score),
                index=i,
            )
            for i, (idx, score) in enumerate(reranked, 1)
            for result in [initial_results[idx]]
        ]

        logger.info(
            "query_completed",
            query=request.query,
            sources=len(sources),
            answer_length=len(answer),
        )

        return QueryResponse(
            answer=answer,
            sources=sources,
            query=request.query,
            model=self._settings.ollama_model,
            tokens_used=None,  # Ollama doesn't always return this
        )

    async def reset_index(self) -> dict:
        """Reset the vector store index.

        Returns:
            Status message.
        """
        await self._ensure_initialized()

        await self._vector_store.delete_all()

        logger.info("vector_store_reset")

        return {"status": "success", "message": "Vector store index cleared"}

    async def health_check(self) -> dict:
        """Check service health.

        Returns:
            Health status dictionary.
        """
        ollama_healthy = await self._ollama_tool.check_health()

        return {
            "status": "healthy" if ollama_healthy else "degraded",
            "ollama": "connected" if ollama_healthy else "disconnected",
            "vector_store": "initialized" if self._initialized else "not_initialized",
        }
