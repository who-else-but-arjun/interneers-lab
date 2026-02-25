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
    product = _repo.create(data)
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


def list_products(page: int = 1, page_size: int = 10) -> tuple[list[Product], int]:
    _ensure_repo()
    return _repo.list_products(page=page, page_size=page_size)


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
        "price": data.get("price", existing.price),
        "brand": data.get("brand", existing.brand),
        "quantity": data.get("quantity", existing.quantity),
    }
    updated = _repo.update(product_id, merged)
    return updated, None


def delete(product_id: str) -> bool:
    _ensure_repo()
    return _repo.delete(product_id)
