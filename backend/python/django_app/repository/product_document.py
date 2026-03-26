from datetime import datetime
from mongoengine import Document, ObjectIdField, StringField, FloatField, IntField, DateTimeField


class ProductDocument(Document):
    meta = {"collection": "products"}
    name = StringField(required=True)
    description = StringField(default="")
    category = StringField(default="")
    category_id = ObjectIdField(default=None)
    price = FloatField(required=True)
    brand = StringField(default="")
    quantity = IntField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
