from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple


@dataclass
class ProductCategory:
    id: str
    title: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_category_data(data: Dict[str, Any], for_update: bool = False) -> Tuple[bool, Dict[str, str]]:
    errors: Dict[str, str] = {}
    if not for_update:
        title = (data.get("title") or "").strip()
        if not title:
            errors["title"] = "Title is required and cannot be empty"
    else:
        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                errors["title"] = "Title cannot be empty"
    return len(errors) == 0, errors
