from datetime import datetime
from mongoengine import Document, ObjectIdField, StringField, DateTimeField, ListField, DictField


class RagChatDocument(Document):
    meta = {"collection": "rag_chats"}
    
    session_id = StringField(required=True)
    title = StringField(default="New Chat")
    messages = ListField(DictField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
