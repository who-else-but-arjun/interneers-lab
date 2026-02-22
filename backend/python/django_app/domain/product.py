import uuid
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Product:
    id: str
    name: str
    description: str
    category: str
    price: float
    brand: str
    quantity: int

    def to_dict(self):
        return asdict(self)


def validate_product_data(data: dict, for_update: bool = False) -> tuple[bool, dict]:
    errors = {}
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

    return len(errors) == 0, errors


def product_from_dict(data: dict, id: Optional[str] = None) -> Product:
    return Product(
        id=id or str(uuid.uuid4()),
        name=(data.get("name") or "").strip(),
        description=(data.get("description") or "").strip(),
        category=(data.get("category") or "").strip(),
        price=float(data.get("price", 0)),
        brand=(data.get("brand") or "").strip(),
        quantity=int(data.get("quantity", 0)),
    )
