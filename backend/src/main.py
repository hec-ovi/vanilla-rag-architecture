"""
Vanilla RAG Architecture - FastAPI Backend

A production-ready local RAG system with semantic reranking.
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Vanilla RAG API",
    description="Local-first RAG system with semantic reranking",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "vanilla-rag-backend"}


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Vanilla RAG Architecture",
        "docs": "/docs",
        "health": "/health",
    }
