from mongoengine import Document, StringField, ListField, DateTimeField
from datetime import datetime


class AIInventoryChatDocument(Document):
    """MongoDB document for AI Inventory Assistant chat sessions"""
    session_id = StringField(required=True)
    title = StringField(default="New Chat")
    messages = ListField(default=list)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'ai_inventory_chats',
        'indexes': ['session_id', '-updated_at']
    }
