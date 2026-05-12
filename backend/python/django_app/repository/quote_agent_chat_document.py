from datetime import datetime
from mongoengine import Document, StringField, ListField, DictField, DateTimeField

class QuoteAgentChatDocument(Document):

    session_id = StringField(required=True)
    title      = StringField(default="New Chat")
    messages   = ListField(DictField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "quote_agent_chats",
        "indexes": ["session_id", "-updated_at"],
    }
