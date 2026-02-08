"""Health check routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core import Settings, get_settings
from src.services import RAGService

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Health check endpoint.

    Returns:
        Health status of the service.
    """
    # Basic health check - just verify we can respond
    return {
        "status": "healthy",
        "service": "vanilla-rag-backend",
        "version": "0.1.0",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> dict:
    """Readiness probe for orchestration.

    Returns:
        Readiness status including dependency health.
    """
    rag_service = RAGService()
    health = await rag_service.health_check()

    return {
        "ready": health["ollama"] == "connected",
        **health,
    }
