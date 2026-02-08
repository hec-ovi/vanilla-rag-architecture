"""RAG API routes for document ingestion and querying."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.core import RAGError, get_settings
from src.models.rag import IngestResponse, QueryRequest, QueryResponse
from src.services import RAGService

router = APIRouter(tags=["RAG"], prefix="/api/v1")


@router.post("/ingest", status_code=status.HTTP_200_OK)
async def ingest_document(
    file: Annotated[UploadFile, File(description="Document to ingest")],
) -> IngestResponse:
    """Ingest a document into the RAG system.

    Supports: .txt, .md, .pdf, .docx, .png, .jpg, .jpeg, .gif, .bmp, .webp

    Args:
        file: Uploaded document file.

    Returns:
        Ingestion result with chunk count.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Validate file type
    rag_service = RAGService()
    if not rag_service._document_service.is_supported(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.filename}",
        )

    try:
        content = await file.read()
        result = await rag_service.ingest_document(content, file.filename)

        if result.status == "error":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        ) from e


@router.post("/query", status_code=status.HTTP_200_OK)
async def query(
    request: QueryRequest,
) -> QueryResponse:
    """Query the RAG system.

    Args:
        request: Query request with question.

    Returns:
        Generated answer with source citations.
    """
    rag_service = RAGService()

    try:
        return await rag_service.query(request)
    except RAGError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        ) from e


@router.post("/reset", status_code=status.HTTP_200_OK)
async def reset_index() -> dict:
    """Reset the vector store index.

    Deletes all ingested documents.

    Returns:
        Status message.
    """
    rag_service = RAGService()

    try:
        return await rag_service.reset_index()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reset failed: {str(e)}",
        ) from e


@router.get("/documents", status_code=status.HTTP_200_OK)
async def list_documents() -> dict:
    """List all ingested documents.

    Returns:
        List of documents (placeholder for future implementation).
    """
    # TODO: Implement document listing with metadata store
    return {"documents": [], "count": 0}
