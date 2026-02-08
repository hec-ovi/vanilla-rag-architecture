"""Conversation storage service."""

import json
import uuid
from pathlib import Path
from threading import Lock

import structlog

from src.core import Settings, get_settings
from src.models.chat import ChatMessage, Conversation

logger = structlog.get_logger()


class ConversationService:
    """Service for managing conversation history."""

    _instance = None
    _lock = Lock()

    def __new__(cls, settings: Settings | None = None):
        """Singleton pattern to ensure single store across app."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings: Settings | None = None):
        """Initialize conversation store.

        Args:
            settings: Application settings.
        """
        if self._initialized:
            return

        self._settings = settings or get_settings()
        self._conversations: dict[str, Conversation] = {}
        self._store_path = Path(self._settings.data_dir) / "conversations.json"
        self._lock = Lock()

        # Load existing conversations
        self._load()
        self._initialized = True

        logger.info("conversation_service_initialized", store_path=str(self._store_path))

    def _load(self) -> None:
        """Load conversations from disk."""
        if not self._store_path.exists():
            return

        try:
            with open(self._store_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for conv_data in data.get("conversations", []):
                conv = Conversation(**conv_data)
                # Convert dict messages to ChatMessage objects
                conv.messages = [
                    ChatMessage(**msg) if isinstance(msg, dict) else msg
                    for msg in conv.messages
                ]
                self._conversations[conv.conversation_id] = conv

            logger.info("conversations_loaded", count=len(self._conversations))
        except Exception as e:
            logger.error("conversation_load_failed", error=str(e))

    def _save(self) -> None:
        """Save conversations to disk."""
        try:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "conversations": [
                    {
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
                    for conv in self._conversations.values()
                ]
            }

            with open(self._store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("conversation_save_failed", error=str(e))

    def create_conversation(self) -> Conversation:
        """Create a new conversation.

        Returns:
            New conversation instance.
        """
        conv_id = str(uuid.uuid4())
        conversation = Conversation(conversation_id=conv_id)

        with self._lock:
            self._conversations[conv_id] = conversation
            self._save()

        logger.debug("conversation_created", conversation_id=conv_id)
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation ID.

        Returns:
            Conversation or None if not found.
        """
        return self._conversations.get(conversation_id)

    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation ID.
            role: Message role (user/assistant).
            content: Message content.

        Returns:
            True if added, False if conversation not found.
        """
        with self._lock:
            conv = self._conversations.get(conversation_id)
            if not conv:
                return False

            conv.add_message(role, content)
            self._save()

        logger.debug("message_added", conversation_id=conversation_id, role=role)
        return True

    def get_or_create_conversation(self, conversation_id: str | None) -> Conversation:
        """Get existing conversation or create new one.

        Args:
            conversation_id: Existing ID or None to create new.

        Returns:
            Conversation instance.
        """
        if conversation_id:
            conv = self.get_conversation(conversation_id)
            if conv:
                return conv

        return self.create_conversation()

    def list_conversations(self) -> list[Conversation]:
        """List all conversations.

        Returns:
            List of conversations, sorted by updated_at desc.
        """
        return sorted(
            self._conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.

        Args:
            conversation_id: Conversation ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            if conversation_id not in self._conversations:
                return False

            del self._conversations[conversation_id]
            self._save()

        logger.info("conversation_deleted", conversation_id=conversation_id)
        return True

    def clear_all(self) -> int:
        """Clear all conversations.

        Returns:
            Number of conversations cleared.
        """
        with self._lock:
            count = len(self._conversations)
            self._conversations.clear()
            self._save()

        logger.info("all_conversations_cleared", count=count)
        return count
