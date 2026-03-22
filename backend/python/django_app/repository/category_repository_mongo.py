from bson import ObjectId
from mongoengine import DoesNotExist

from django_app.domain.product_category import ProductCategory
from django_app.repository.category_document import ProductCategoryDocument
from django_app.repository.category_repository import ProductCategoryRepository


def _doc_to_category(doc: ProductCategoryDocument) -> ProductCategory:
    return ProductCategory(
        id=str(doc.id),
        title=doc.title,
        description=doc.description,
    )


class MongoProductCategoryRepository(ProductCategoryRepository):
    def create(self, data: dict) -> ProductCategory:
        doc = ProductCategoryDocument(
            title=(data.get("title") or "").strip(),
            description=(data.get("description") or "").strip(),
        )
        doc.save()
        doc.reload()
        return _doc_to_category(doc)

    def get_by_id(self, category_id: str) -> ProductCategory | None:
        try:
            doc = ProductCategoryDocument.objects.get(id=ObjectId(category_id))
            return _doc_to_category(doc)
        except (DoesNotExist, TypeError, ValueError):
            return None

    def list_all(self) -> list[ProductCategory]:
        docs = ProductCategoryDocument.objects.all()
        return [_doc_to_category(d) for d in docs]

    def update(self, category_id: str, data: dict) -> ProductCategory | None:
        try:
            doc = ProductCategoryDocument.objects.get(id=ObjectId(category_id))
        except (DoesNotExist, TypeError, ValueError):
            return None
        if "title" in data:
            doc.title = (data["title"] or "").strip()
        if "description" in data:
            doc.description = (data["description"] or "").strip()
        doc.save()
        doc.reload()
        return _doc_to_category(doc)

    def delete(self, category_id: str) -> bool:
        try:
            doc = ProductCategoryDocument.objects.get(id=ObjectId(category_id))
            doc.delete()
            return True
        except (DoesNotExist, TypeError, ValueError):
            return False
