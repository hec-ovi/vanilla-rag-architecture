"""Chat API routes with conversation memory."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, status

from src.core import RAGError
from src.models.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ConversationListResponse,
)
from src.services import RAGService
from src.services.conversation_service import ConversationService

router = APIRouter(tags=["Chat"], prefix="/api/v1")


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat(
    request: ChatQueryRequest,
) -> ChatQueryResponse:
    """Chat with the RAG system with conversation memory.

    If conversation_id is provided, the message is added to that conversation.
    If not provided, a new conversation is created.

    Returns:
        Chat response with conversation_id for follow-up messages.
    """
    rag_service = RAGService()

    try:
        return await rag_service.chat(request)
    except RAGError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        ) from e


@router.get("/conversations", status_code=status.HTTP_200_OK)
async def list_conversations() -> ConversationListResponse:
    """List all conversations.

    Returns:
        List of conversations sorted by most recent.
    """
    service = ConversationService()
    conversations = service.list_conversations()

    return ConversationListResponse(
        conversations=conversations,
        count=len(conversations),
    )


@router.get("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_conversation(conversation_id: str) -> dict:
    """Get a specific conversation.

    Args:
        conversation_id: Conversation ID.

    Returns:
        Conversation details.
    """
    service = ConversationService()
    conv = service.get_conversation(conversation_id)

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    return {
        "conversation_id": conv.conversation_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in conv.messages
        ],
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
    }


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(conversation_id: str) -> dict:
    """Delete a conversation.

    Args:
        conversation_id: Conversation ID to delete.

    Returns:
        Status message.
    """
    service = ConversationService()
    success = service.delete_conversation(conversation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}


@router.post("/conversations/clear", status_code=status.HTTP_200_OK)
async def clear_all_conversations() -> dict:
    """Clear all conversations.

    Returns:
        Status message with count of deleted conversations.
    """
    service = ConversationService()
    count = service.clear_all()

    return {
        "status": "success",
        "message": f"Deleted {count} conversations",
        "count": count,
    }
