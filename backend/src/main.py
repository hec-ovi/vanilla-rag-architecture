"""
Vanilla RAG Architecture - FastAPI Backend

A production-ready local RAG system with semantic reranking.
"""

from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core import RAGError, get_settings
from src.routes import health_router, rag_router

logger = structlog.get_logger()


def _create_test_data() -> None:
    """Create test data file if it doesn't exist."""
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    test_file = data_dir / "rag_techniques_test.txt"

    if not test_file.exists():
        content = """# Advanced RAG Techniques - 2026 Knowledge Base

## HyPE (Hypothetical Prompt Expansion)

HyPE is a technique where the system generates multiple hypothetical versions of the user's query to improve retrieval coverage. By expanding a single query into variations with different phrasings, synonyms, and perspectives, the system can retrieve documents that might not match the original query but contain relevant information.

Example: Query "AI safety" expands to "artificial intelligence safety", "machine learning safety concerns", "ensuring safe AI deployment", etc.

## HyDE (Hypothetical Document Embeddings)

HyDE takes the opposite approach - instead of expanding the query, it generates a hypothetical ideal document that would answer the query, then embeds that document to retrieve similar real documents. This bridges the gap between query and document representations since queries and documents often use different language patterns.

The process: Query → Generate hypothetical answer → Embed hypothetical answer → Retrieve similar real documents.

## Multi-Query Retrieval

Multi-query retrieval generates multiple sub-questions from a complex query and retrieves documents for each. The results are then merged and deduplicated. This is particularly effective for questions that span multiple topics or require combining information from different sources.

## Contextual Compression

Contextual compression reduces retrieved documents to only the most relevant parts before sending to the LLM. This saves tokens and reduces noise. Techniques include:
- Extractive compression: Select most relevant sentences
- Abstractive compression: Generate summary of relevant parts
- Reranking: Score and filter chunks

## Semantic Reranking

Semantic reranking uses cross-encoder models to rescore retrieved documents. Unlike bi-encoders (which embed query and docs separately), cross-encoders process query+doc together, capturing subtle relevance signals. This typically improves retrieval precision by 15-30%.

The workflow: Vector search (top-20) → Cross-encoder rerank → Select top-5.

## Recursive Retrieval

Recursive retrieval starts with broad retrieval, then uses those results to generate more specific queries for deeper retrieval. This mimics how humans research - first get overview, then drill into specifics.

Useful for: Complex multi-hop questions, research tasks, exploratory queries.

## Fusion Retrieval

Fusion retrieval combines multiple retrieval methods:
- Dense retrieval (embeddings)
- Sparse retrieval (BM25/TF-IDF)
- Graph-based retrieval
- Keyword matching

Results are merged using reciprocal rank fusion or learned fusion models.

## Self-RAG

Self-RAG is a technique where the LLM critiques its own retrieval and generation. It can:
- Request additional retrieval if context is insufficient
- Reject answering if sources are unreliable
- Cite sources explicitly
- Evaluate answer completeness

This reduces hallucination and improves answer quality significantly.

## Corrective RAG (CRAG)

CRAG adds a retrieval evaluator that scores retrieved documents for relevance. If documents are irrelevant, it triggers:
- Web search for external knowledge
- Query rewriting for better retrieval
- Fallback to LLM knowledge (with disclaimer)

## ReAct (Reasoning + Acting)

ReAct combines reasoning and action in an interleaved manner. The LLM:
1. Reasons about what it needs to know
2. Takes action (retrieves, calculates, searches)
3. Observes results
4. Repeats until answer found

This is the foundation of many agentic RAG systems.

## Tree of Thoughts (ToT)

ToT maintains multiple reasoning paths (a tree) and explores them systematically. For RAG, this means:
- Generate multiple query variations
- Retrieve for each
- Evaluate which branch is most promising
- Explore deeper or backtrack

## Graph RAG

Graph RAG builds a knowledge graph from documents and traverses it during retrieval. Instead of vector similarity, it uses:
- Entity relationships
- Semantic connections
- Hierarchical document structure

This excels for interconnected knowledge domains like legal, medical, or technical documentation.

---

Test Questions:
1. What is the difference between HyPE and HyDE?
2. How does contextual compression save tokens?
3. What is the typical improvement from semantic reranking?
4. Explain the ReAct pattern in RAG systems.
5. When would you use recursive retrieval vs multi-query retrieval?
"""
        test_file.write_text(content)
        logger.info("test_data_created", path=str(test_file))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("starting_vanilla_rag_backend")
    _create_test_data()
    yield
    # Shutdown
    logger.info("shutting_down_vanilla_rag_backend")


app = FastAPI(
    title="Vanilla RAG API",
    description="Local-first RAG system with semantic reranking",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(rag_router)


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> dict:
    """Root endpoint.

    Returns:
        API information and available endpoints.
    """
    return {
        "message": "Vanilla RAG Architecture",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "ingest": "POST /api/v1/ingest",
            "query": "POST /api/v1/query",
            "reset": "POST /api/v1/reset",
        },
    }


@app.exception_handler(RAGError)
async def rag_error_handler(request, exc: RAGError):
    """Handle RAG domain errors."""
    logger.error("rag_error", message=exc.message, details=exc.details)
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "details": exc.details},
    )
