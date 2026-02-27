from mongoengine import Document, StringField


class ProductCategoryDocument(Document):
    meta = {"collection": "product_categories"}
    title = StringField(required=True)
    description = StringField(default="")
