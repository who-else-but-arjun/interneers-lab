from typing import List, Optional, Dict, Any
from datetime import datetime
from .ai_inventory_chat_document import AIInventoryChatDocument


class AIInventoryChatRepositoryMongo:
    """Repository for AI Inventory Assistant chat persistence in MongoDB"""
    
    @staticmethod
    def get_chats_by_session(session_id: str) -> List[Dict[str, Any]]:
        """Get all chats for a session, ordered by updated_at descending"""
        chats = AIInventoryChatDocument.objects(session_id=session_id).order_by('-updated_at')
        return [{
            'id': str(chat.id),
            'title': chat.title,
            'messages': chat.messages,
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat()
        } for chat in chats]
    
    @staticmethod
    def create_chat(session_id: str, title: str = "New Chat") -> Dict[str, Any]:
        """Create a new chat session"""
        chat = AIInventoryChatDocument(
            session_id=session_id,
            title=title,
            messages=[]
        )
        chat.save()
        return {
            'id': str(chat.id),
            'title': chat.title,
            'messages': chat.messages,
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat()
        }
    
    @staticmethod
    def get_chat(chat_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific chat by ID and session"""
        try:
            chat = AIInventoryChatDocument.objects.get(id=chat_id, session_id=session_id)
            return {
                'id': str(chat.id),
                'title': chat.title,
                'messages': chat.messages,
                'created_at': chat.created_at.isoformat(),
                'updated_at': chat.updated_at.isoformat()
            }
        except:
            return None
    
    @staticmethod
    def update_chat(chat_id: str, session_id: str, messages: List[Dict], title: str = None) -> bool:
        """Update chat messages and optionally title"""
        try:
            chat = AIInventoryChatDocument.objects.get(id=chat_id, session_id=session_id)
            chat.messages = messages
            if title:
                chat.title = title
            chat.updated_at = datetime.utcnow()
            chat.save()
            return True
        except:
            return False
    
    @staticmethod
    def delete_chat(chat_id: str, session_id: str) -> bool:
        """Delete a chat session"""
        chat = AIInventoryChatDocument.objects.filter(id=chat_id, session_id=session_id).first()
        if chat is None:
            return False
        chat.delete()
        return True
