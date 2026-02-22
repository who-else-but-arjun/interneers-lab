from typing import Optional
from django_app.domain.product import (
    Product,
    validate_product_data,
    product_from_dict,
)

_store: dict[str, Product] = {}


def create(data: dict) -> tuple[Optional[Product], Optional[dict]]:
    ok, errors = validate_product_data(data, for_update=False)
    if not ok:
        return None, errors
    product = product_from_dict(data)
    _store[product.id] = product
    return product, None


def create_many(items: list) -> tuple[list[Product], list[dict]]:
    created = []
    errors = []
    for i, data in enumerate(items):
        if not isinstance(data, dict):
            errors.append({"index": i, "details": {"_": "Each item must be an object"}})
            continue
        product, err = create(data)
        if err:
            errors.append({"index": i, "details": err})
        else:
            created.append(product)
    return created, errors


def get_by_id(product_id: str) -> Optional[Product]:
    return _store.get(product_id)


def list_products(page: int = 1, page_size: int = 10) -> tuple[list[Product], int]:
    items = list(_store.values())
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    if page_size <= 0:
        page_size = total
        end = total
    page_items = items[start:end]
    return page_items, total


def update(product_id: str, data: dict) -> tuple[Optional[Product], Optional[dict]]:
    existing = _store.get(product_id)
    if not existing:
        return None, {"_error": "Product not found"}
    ok, errors = validate_product_data(data, for_update=True)
    if not ok:
        return None, errors
    updated = product_from_dict(
        {
            "name": data.get("name", existing.name),
            "description": data.get("description", existing.description),
            "category": data.get("category", existing.category),
            "price": data.get("price", existing.price),
            "brand": data.get("brand", existing.brand),
            "quantity": data.get("quantity", existing.quantity),
        },
        id=existing.id,
    )
    _store[product_id] = updated
    return updated, None


def delete(product_id: str) -> bool:
    if product_id in _store:
        del _store[product_id]
        return True
    return False
