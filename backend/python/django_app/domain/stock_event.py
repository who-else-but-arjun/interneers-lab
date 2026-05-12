import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class StockEvent:
    id: str
    event_type: str
    expected_date: str
    description: str
    priority: str
    status: str = "pending"
    event_name: str = ""
    products: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'id': self.id,
            'event_name': self.event_name,
            'event_type': self.event_type,
            'expected_date': self.expected_date,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'products': self.products,
            'created_at': self.created_at.isoformat() + "Z" if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


VALID_EVENT_TYPES = ['Delivery', 'Restock', 'Sale', 'Return', 'Audit', 'Expiry', 'Reorder']
VALID_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
VALID_STATUSES = ['pending', 'completed', 'cancelled']


def validate_stock_event_data(data: dict, for_update: bool = False) -> tuple[bool, dict]:
    errors = {}
    
    if not for_update:
        event_type = (data.get("event_type") or "").strip()
        if not event_type:
            errors["event_type"] = "Event type is required"
        elif event_type not in VALID_EVENT_TYPES:
            errors["event_type"] = f"Event type must be one of: {VALID_EVENT_TYPES}"
            
        expected_date = (data.get("expected_date") or "").strip()
        if not expected_date:
            errors["expected_date"] = "Expected date is required"
            
        products = data.get("products", [])
        if not products:
            errors["products"] = "At least one product is required"
    else:
        if "event_type" in data:
            event_type = (data.get("event_type") or "").strip()
            if event_type and event_type not in VALID_EVENT_TYPES:
                errors["event_type"] = f"Event type must be one of: {VALID_EVENT_TYPES}"
                
        if "priority" in data:
            priority = (data.get("priority") or "").strip()
            if priority and priority not in VALID_PRIORITIES:
                errors["priority"] = f"Priority must be one of: {VALID_PRIORITIES}"
                
        if "status" in data:
            status = (data.get("status") or "").strip()
            if status and status not in VALID_STATUSES:
                errors["status"] = f"Status must be one of: {VALID_STATUSES}"
    
    return len(errors) == 0, errors


def stock_event_from_dict(
    data: dict,
    id: Optional[str] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
) -> StockEvent:
    return StockEvent(
        id=id or str(uuid.uuid4()),
        event_name=data.get("event_name", ""),
        event_type=(data.get("event_type") or "").strip(),
        expected_date=(data.get("expected_date") or "").strip(),
        description=(data.get("description") or "").strip(),
        priority=(data.get("priority") or "Medium").strip(),
        status=(data.get("status") or "pending").strip(),
        products=data.get("products", []),
        created_at=created_at,
        updated_at=updated_at,
    )
