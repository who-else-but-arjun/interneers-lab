from datetime import datetime
from bson import ObjectId
from mongoengine import DoesNotExist

from django_app.domain.product import Product, product_from_dict
from django_app.repository.product_document import ProductDocument
from django_app.repository.product_repository import ProductRepository


def _doc_to_product(doc: ProductDocument) -> Product:
    return product_from_dict(
        {
            "name": doc.name,
            "description": doc.description,
            "category": doc.category,
            "price": doc.price,
            "brand": doc.brand,
            "quantity": doc.quantity,
        },
        id=str(doc.id),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


class MongoProductRepository(ProductRepository):
    def create(self, data: dict) -> Product:
        doc = ProductDocument(
            name=(data.get("name") or "").strip(),
            description=(data.get("description") or "").strip(),
            category=(data.get("category") or "").strip(),
            price=float(data.get("price", 0)),
            brand=(data.get("brand") or "").strip(),
            quantity=int(data.get("quantity", 0)),
        )
        doc.save()
        doc.reload()
        return _doc_to_product(doc)

    def get_by_id(self, product_id: str) -> Product | None:
        try:
            doc = ProductDocument.objects.get(id=ObjectId(product_id))
            return _doc_to_product(doc)
        except (DoesNotExist, TypeError, ValueError):
            return None

    def list_products(self, page: int, page_size: int) -> tuple[list[Product], int]:
        qs = ProductDocument.objects.order_by("-created_at")
        total = qs.count()
        start = (page - 1) * page_size
        if page_size <= 0:
            page_size = max(1, total)
        docs = list(qs.skip(start).limit(page_size))
        return [_doc_to_product(d) for d in docs], total

    def update(self, product_id: str, data: dict) -> Product | None:
        try:
            doc = ProductDocument.objects.get(id=ObjectId(product_id))
        except (DoesNotExist, TypeError, ValueError):
            return None
        if "name" in data:
            doc.name = (data["name"] or "").strip()
        if "description" in data:
            doc.description = (data["description"] or "").strip()
        if "category" in data:
            doc.category = (data["category"] or "").strip()
        if "price" in data:
            doc.price = float(data["price"])
        if "brand" in data:
            doc.brand = (data["brand"] or "").strip()
        if "quantity" in data:
            doc.quantity = int(data["quantity"])
        doc.updated_at = datetime.utcnow()
        doc.save()
        doc.reload()
        return _doc_to_product(doc)

    def delete(self, product_id: str) -> bool:
        try:
            doc = ProductDocument.objects.get(id=ObjectId(product_id))
            doc.delete()
            return True
        except (DoesNotExist, TypeError, ValueError):
            return False
