from datetime import datetime
from mongoengine import Document, ObjectIdField, StringField, IntField, DateTimeField, ListField, DictField


class StockEventDocument(Document):
    meta = {"collection": "stock_events"}
    event_name = StringField(default="")
    event_type = StringField(required=True)
    expected_date = StringField(required=True)
    description = StringField(default="")
    priority = StringField(default="Medium")
    status = StringField(default="pending")
    products = ListField(DictField(), default=[])
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
