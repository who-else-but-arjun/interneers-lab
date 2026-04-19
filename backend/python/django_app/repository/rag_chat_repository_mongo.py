from typing import List, Optional, Dict, Any
from datetime import datetime
from .rag_chat_document import RagChatDocument


class RagChatRepositoryMongo:
    
    @staticmethod
    def get_chats_by_session(session_id: str) -> List[Dict[str, Any]]:
        chats = RagChatDocument.objects(session_id=session_id).order_by('-updated_at')
        return [{
            'id': str(chat.id),
            'title': chat.title,
            'messages': chat.messages,
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat()
        } for chat in chats]
    
    @staticmethod
    def create_chat(session_id: str, title: str = "New Chat") -> Dict[str, Any]:
        chat = RagChatDocument(
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
        try:
            chat = RagChatDocument.objects.get(id=chat_id, session_id=session_id)
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
        try:
            chat = RagChatDocument.objects.get(id=chat_id, session_id=session_id)
            chat.messages = messages
            chat.updated_at = datetime.utcnow()
            if title:
                chat.title = title
            chat.save()
            return True
        except:
            return False
    
    @staticmethod
    def delete_chat(chat_id: str, session_id: str) -> bool:
        try:
            chat = RagChatDocument.objects.get(id=chat_id, session_id=session_id)
            chat.delete()
            return True
        except:
            return False
    
    @staticmethod
    def save_messages(chat_id: str, session_id: str, messages: List[Dict]) -> bool:
        return RagChatRepositoryMongo.update_chat(chat_id, session_id, messages)
