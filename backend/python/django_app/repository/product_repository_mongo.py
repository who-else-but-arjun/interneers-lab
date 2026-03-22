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
            "policy": doc.policy if doc.policy else {
                "warranty_period": "",
                "return_window": "",
                "refund_policy": "",
                "vendor_faq_link": ""
            },
        },
        id=str(doc.id),
        category_id=str(doc.category_id) if doc.category_id else None,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


class MongoProductRepository(ProductRepository):
    def create(self, data: dict) -> Product:
        cid = None
        if data.get("category_id"):
            try:
                cid = ObjectId(data["category_id"])
            except (TypeError, ValueError):
                pass
        doc = ProductDocument(
            name=(data.get("name") or "").strip(),
            description=(data.get("description") or "").strip(),
            category=(data.get("category") or "").strip(),
            category_id=cid,
            price=float(data.get("price", 0)),
            brand=(data.get("brand") or "").strip(),
            quantity=int(data.get("quantity", 0)),
            policy=data.get("policy") or {
                "warranty_period": "",
                "return_window": "",
                "refund_policy": "",
                "vendor_faq_link": ""
            },
        )
        doc.save()
        doc.reload()
        return _doc_to_product(doc)

    def find_by_identity(self, name: str, brand: str, category: str) -> Product | None:
        """
        Look up an existing product by a stable identity:
        - name (case-sensitive as stored)
        - brand
        - optional category label
        """
        qs = ProductDocument.objects(
            name=(name or "").strip(),
            brand=(brand or "").strip(),
        )
        cat = (category or "").strip()
        if cat:
            qs = qs.filter(category=cat)
        doc = qs.first()
        if not doc:
            return None
        return _doc_to_product(doc)

    def get_by_id(self, product_id: str) -> Product | None:
        try:
            doc = ProductDocument.objects.get(id=ObjectId(product_id))
            return _doc_to_product(doc)
        except (DoesNotExist, TypeError, ValueError):
            return None

    def list_products(
        self, page: int, page_size: int, category_ids: list[str] | None = None
    ) -> tuple[list[Product], int]:
        qs = ProductDocument.objects.order_by("-created_at")
        if category_ids:
            try:
                oids = [ObjectId(cid) for cid in category_ids]
                qs = qs.filter(category_id__in=oids)
            except (TypeError, ValueError):
                pass
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
        if "category_id" in data:
            val = data["category_id"]
            try:
                doc.category_id = ObjectId(val) if val else None
            except (TypeError, ValueError):
                doc.category_id = None
        if "price" in data:
            doc.price = float(data["price"])
        if "brand" in data:
            doc.brand = (data["brand"] or "").strip()
        if "quantity" in data:
            doc.quantity = int(data["quantity"])
        if "policy" in data:
            doc.policy = data["policy"] if data["policy"] else {
                "warranty_period": "",
                "return_window": "",
                "refund_policy": "",
                "vendor_faq_link": ""
            }
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
