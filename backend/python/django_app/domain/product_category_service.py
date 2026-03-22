from typing import Optional, Dict, Any, Tuple, List
from django_app.domain.product_category import (
    ProductCategory,
    validate_category_data,
)
from django_app.repository.category_repository import ProductCategoryRepository

_cat_repo: Optional[ProductCategoryRepository] = None


def set_repository(repo: ProductCategoryRepository) -> None:
    global _cat_repo
    _cat_repo = repo


def _ensure_repo() -> None:
    if _cat_repo is None:
        raise RuntimeError("ProductCategory repository not initialized.")


def create(data: Dict[str, Any]) -> Tuple[Optional[ProductCategory], Optional[Dict[str, Any]]]:
    _ensure_repo()
    ok, errors = validate_category_data(data, for_update=False)
    if not ok:
        return None, errors
    category = _cat_repo.create(data)
    return category, None


def get_by_id(category_id: str) -> Optional[ProductCategory]:
    _ensure_repo()
    return _cat_repo.get_by_id(category_id)


def list_all() -> List[ProductCategory]:
    _ensure_repo()
    return _cat_repo.list_all()


def update(category_id: str, data: Dict[str, Any]) -> Tuple[Optional[ProductCategory], Optional[Dict[str, Any]]]:
    _ensure_repo()
    existing = _cat_repo.get_by_id(category_id)
    if not existing:
        return None, {"_error": "Category not found"}
    ok, errors = validate_category_data(data, for_update=True)
    if not ok:
        return None, errors
    merged = {
        "title": data.get("title", existing.title),
        "description": data.get("description", existing.description),
    }
    updated = _cat_repo.update(category_id, merged)
    return updated, None


def delete(category_id: str) -> bool:
    _ensure_repo()
    return _cat_repo.delete(category_id)
