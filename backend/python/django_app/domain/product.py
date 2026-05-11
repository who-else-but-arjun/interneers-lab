import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    category: str
    price: float
    brand: str
    quantity: int
    policy: dict
    category_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.isoformat() + "Z"
        return value.isoformat()

    @field_serializer("policy")
    def serialize_policy(self, value: dict) -> dict:
        return dict(value) if hasattr(value, "to_mongo") else value

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")


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
        except Exception:
            errors["price"] = "Price must be a valid number greater than 0"

    if not for_update and "price" not in data:
        errors["price"] = "Price is required"

    if "quantity" in data:
        try:
            quantity = data["quantity"]
            if not isinstance(quantity, int):
                quantity = int(quantity)
            if quantity < 0:
                errors["quantity"] = "Quantity must be 0 or greater"
        except Exception:
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
    data: dict,
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
        policy=data.get("policy") or {
            "warranty_period": "",
            "return_window": "",
            "refund_policy": "",
            "vendor_faq_link": ""
        },
        created_at=created_at,
        updated_at=updated_at,
    )
