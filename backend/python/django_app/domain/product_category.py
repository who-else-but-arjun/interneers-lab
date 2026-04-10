from dataclasses import dataclass, asdict


@dataclass
class ProductCategory:
    id: str
    title: str
    description: str

    def to_dict(self):
        return asdict(self)


def validate_category_data(data: dict, for_update: bool = False) -> tuple[bool, dict]:
    errors = {}
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
