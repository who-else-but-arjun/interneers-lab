import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, Tuple


@dataclass
class Product:
    id: str
    name: str
    description: str
    category: str
    price: float
    brand: str
    quantity: int
    category_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ("created_at", "updated_at"):
            if d.get(k) is not None:
                d[k] = d[k].isoformat() + "Z" if d[k].tzinfo is None else d[k].isoformat()
        return d


def validate_product_data(data: Dict[str, Any], for_update: bool = False) -> Tuple[bool, Dict[str, str]]:
    errors: Dict[str, str] = {}
    if not for_update:
        name = (data.get("name") or "").strip()
        if not name:
            errors["name"] = "Name is required and cannot be empty"
    else:
        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                errors["name"] = "Name cannot be empty"

    if "price" in data:
        try:
            price = float(data["price"])
            if price <= 0:
                errors["price"] = "Price must be greater than 0"
        except (TypeError, ValueError):
            errors["price"] = "Price must be a valid number greater than 0"

    if not for_update and "price" not in data:
        errors["price"] = "Price is required"

    if "quantity" in data:
        try:
            qty = data["quantity"]
            if not isinstance(qty, int):
                qty = int(qty)
            if qty < 0:
                errors["quantity"] = "Quantity must be 0 or greater"
        except (TypeError, ValueError):
            errors["quantity"] = "Quantity must be a valid non-negative integer"

    if not for_update and "quantity" not in data:
        errors["quantity"] = "Quantity is required"

    if not for_update:
        brand = (data.get("brand") or "").strip()
        if not brand:
            errors["brand"] = "Brand is required and cannot be empty"
    else:
        if "brand" in data:
            brand = (data.get("brand") or "").strip()
            if not brand:
                errors["brand"] = "Brand cannot be empty"

    return len(errors) == 0, errors


def product_from_dict(
    data: Dict[str, Any],
    id: Optional[str] = None,
    category_id: Optional[str] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
) -> Product:
    cid = category_id
    if cid is None and data.get("category_id") is not None:
        cid = str(data["category_id"])
    return Product(
        id=id or str(uuid.uuid4()),
        name=(data.get("name") or "").strip(),
        description=(data.get("description") or "").strip(),
        category=(data.get("category") or "").strip(),
        category_id=cid,
        price=float(data.get("price", 0)),
        brand=(data.get("brand") or "").strip(),
        quantity=int(data.get("quantity", 0)),
        created_at=created_at,
        updated_at=updated_at,
    )
