from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
from mongoengine import DoesNotExist

from django_app.domain.stock_event import StockEvent, stock_event_from_dict
from django_app.repository.stock_event_document import StockEventDocument
from django_app.repository.stock_event_repository import StockEventRepository


def _doc_to_stock_event(doc: StockEventDocument) -> StockEvent:
    return stock_event_from_dict(
        {
            "event_name": doc.event_name or "",
            "event_type": doc.event_type,
            "expected_date": doc.expected_date,
            "description": doc.description,
            "priority": doc.priority,
            "status": doc.status,
            "products": doc.products or [],
        },
        id=str(doc.id),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


class MongoStockEventRepository(StockEventRepository):
    def create(self, data: dict) -> StockEvent:
        products = data.get("products", [])
        doc = StockEventDocument(
            event_name=data.get("event_name", ""),
            event_type=(data.get("event_type") or "").strip(),
            expected_date=(data.get("expected_date") or "").strip(),
            description=(data.get("description") or "").strip(),
            priority=(data.get("priority") or "Medium").strip(),
            status=(data.get("status") or "pending").strip(),
            products=products,
        )
        doc.save()
        return _doc_to_stock_event(doc)

    def get_by_id(self, event_id: str) -> Optional[StockEvent]:
        try:
            doc = StockEventDocument.objects.get(id=ObjectId(event_id))
            return _doc_to_stock_event(doc)
        except (DoesNotExist, TypeError, ValueError):
            return None

    def list_events(
        self,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> tuple[List[StockEvent], int]:
        qs = StockEventDocument.objects.order_by("-created_at")
        
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if event_type:
            qs = qs.filter(event_type=event_type)
            
        total = qs.count()
        start = (page - 1) * page_size
        if page_size <= 0:
            page_size = max(1, total)
        docs = list(qs.skip(start).limit(page_size))
        return [_doc_to_stock_event(d) for d in docs], total

    def update(self, event_id: str, data: dict) -> Optional[StockEvent]:
        try:
            doc = StockEventDocument.objects.get(id=ObjectId(event_id))
        except (DoesNotExist, TypeError, ValueError):
            return None
            
        if "event_name" in data:
            doc.event_name = (data["event_name"] or "").strip()
        if "event_type" in data:
            doc.event_type = (data["event_type"] or "").strip()
        if "expected_date" in data:
            doc.expected_date = (data["expected_date"] or "").strip()
        if "description" in data:
            doc.description = (data["description"] or "").strip()
        if "priority" in data:
            doc.priority = (data["priority"] or "Medium").strip()
        if "status" in data:
            doc.status = (data["status"] or "pending").strip()
        if "products" in data:
            doc.products = data["products"] or []
                
        doc.updated_at = datetime.now()
        doc.save()
        return _doc_to_stock_event(doc)

    def delete(self, event_id: str) -> bool:
        try:
            doc = StockEventDocument.objects.get(id=ObjectId(event_id))
            doc.delete()
            return True
        except (DoesNotExist, TypeError, ValueError):
            return False

    def get_upcoming_events(self, days: int = 30) -> List[StockEvent]:
        from mongoengine.queryset.visitor import Q
        
        today = datetime.now()
        future = today + timedelta(days=days)
        
        docs = StockEventDocument.objects.filter(status="pending")
        events = [_doc_to_stock_event(d) for d in docs]
        
        upcoming = []
        for event in events:
            try:
                event_date = datetime.strptime(event.expected_date, "%b %d, %Y")
                if today <= event_date <= future:
                    upcoming.append(event)
            except ValueError:
                continue
                
        return sorted(upcoming, key=lambda e: e.expected_date)
