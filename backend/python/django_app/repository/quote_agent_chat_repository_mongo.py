from typing import Any, Dict, List, Optional
from datetime import datetime

from .quote_agent_chat_document import QuoteAgentChatDocument

class QuoteAgentChatRepositoryMongo:

    @staticmethod
    def get_chats_by_session(session_id: str) -> List[Dict[str, Any]]:

        chats = QuoteAgentChatDocument.objects(
            session_id=session_id
        ).order_by("-updated_at")
        return [QuoteAgentChatRepositoryMongo._serialize(c) for c in chats]

    @staticmethod
    def get_chat(chat_id: str, session_id: str) -> Optional[Dict[str, Any]]:

        try:
            chat = QuoteAgentChatDocument.objects.get(
                id=chat_id, session_id=session_id
            )
            return QuoteAgentChatRepositoryMongo._serialize(chat)
        except Exception:
            return None

    @staticmethod
    def create_chat(session_id: str, title: str = "New Chat") -> Dict[str, Any]:

        chat = QuoteAgentChatDocument(
            session_id=session_id,
            title=title,
            messages=[],
        )
        chat.save()
        return QuoteAgentChatRepositoryMongo._serialize(chat)

    @staticmethod
    def update_chat(
        chat_id: str,
        session_id: str,
        messages: List[Dict],
        title: Optional[str] = None,
    ) -> bool:

        try:
            chat = QuoteAgentChatDocument.objects.get(
                id=chat_id, session_id=session_id
            )
            chat.messages   = messages
            chat.updated_at = datetime.utcnow()
            if title:
                chat.title = title
            chat.save()
            return True
        except Exception:
            return False

    @staticmethod
    def delete_chat(chat_id: str, session_id: str) -> bool:

        try:
            chat = QuoteAgentChatDocument.objects.get(
                id=chat_id, session_id=session_id
            )
            chat.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def save_messages(
        chat_id: str, session_id: str, messages: List[Dict]
    ) -> bool:

        return QuoteAgentChatRepositoryMongo.update_chat(
            chat_id, session_id, messages
        )

    @staticmethod
    def _serialize(chat: QuoteAgentChatDocument) -> Dict[str, Any]:
        return {
            "id":         str(chat.id),
            "title":      chat.title,
            "messages":   chat.messages,
            "created_at": chat.created_at.isoformat(),
            "updated_at": chat.updated_at.isoformat(),
        }
