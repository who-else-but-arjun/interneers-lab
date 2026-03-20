from typing import Optional
from django_app.domain.product import (
    Product,
    validate_product_data,
    product_from_dict,
)
from django_app.repository.product_repository import ProductRepository

_repo: Optional[ProductRepository] = None


def set_repository(repository: ProductRepository) -> None:
    global _repo
    _repo = repository


def _ensure_repo():
    if _repo is None:
        raise RuntimeError("Product repository not initialized; ensure Django app is loaded.")


def create(data: dict) -> tuple[Optional[Product], Optional[dict]]:
    _ensure_repo()
    ok, errors = validate_product_data(data, for_update=False)
    if not ok:
        return None, errors

    payload = dict(data)
    if payload.get("category_id") and not isinstance(payload["category_id"], (str, type(None))):
        payload["category_id"] = str(payload["category_id"])

    name = (payload.get("name") or "").strip()
    brand = (payload.get("brand") or "").strip()
    category = (payload.get("category") or "").strip()

    existing: Optional[Product] = None
    if name and brand:
        existing = _repo.find_by_identity(name=name, brand=brand, category=category)

    if existing:
        # Safely determine increment for quantity; default to 0 if not provided.
        increment_raw = payload.get("quantity", 0)
        try:
            increment = int(increment_raw)
        except (TypeError, ValueError):
            increment = 0
        new_quantity = max(0, (existing.quantity or 0) + increment)
        merged = {
            "name": existing.name,
            "description": payload.get("description", existing.description),
            "category": category or existing.category,
            "category_id": payload.get("category_id") or existing.category_id,
            "price": payload.get("price", existing.price),
            "brand": existing.brand,
            "quantity": new_quantity,
            "policy": payload.get("policy", existing.policy) if payload.get("policy") else existing.policy,
        }
        updated = _repo.update(existing.id, merged)
        return updated, None

    product = _repo.create(payload)
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
    _ensure_repo()
    return _repo.get_by_id(product_id)


def list_products(
    page: int = 1, page_size: int = 10, category_ids: list[str] | None = None
) -> tuple[list[Product], int]:
    _ensure_repo()
    return _repo.list_products(page=page, page_size=page_size, category_ids=category_ids)


def update(product_id: str, data: dict) -> tuple[Optional[Product], Optional[dict]]:
    _ensure_repo()
    existing = _repo.get_by_id(product_id)
    if not existing:
        return None, {"_error": "Product not found"}
    ok, errors = validate_product_data(data, for_update=True)
    if not ok:
        return None, errors
    merged = {
        "name": data.get("name", existing.name),
        "description": data.get("description", existing.description),
        "category": data.get("category", existing.category),
        "category_id": data.get("category_id") if "category_id" in data else existing.category_id,
        "price": data.get("price", existing.price),
        "brand": data.get("brand", existing.brand),
        "quantity": data.get("quantity", existing.quantity),
        "policy": data.get("policy", existing.policy) if data.get("policy") else existing.policy,
    }
    updated = _repo.update(product_id, merged)
    return updated, None


def delete(product_id: str) -> bool:
    _ensure_repo()
    return _repo.delete(product_id)
