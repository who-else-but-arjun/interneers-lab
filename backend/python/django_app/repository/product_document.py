from datetime import datetime
from mongoengine import Document, ObjectIdField, StringField, FloatField, IntField, DateTimeField, DictField


class ProductDocument(Document):
    meta = {"collection": "products"}
    name = StringField(required=True)
    description = StringField(default="")
    category = StringField(default="")
    category_id = ObjectIdField(default=None)
    price = FloatField(required=True)
    brand = StringField(default="")
    quantity = IntField(required=True)
    policy = DictField(default=dict)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
