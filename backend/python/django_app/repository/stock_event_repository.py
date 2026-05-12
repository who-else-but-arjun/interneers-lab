from abc import ABC, abstractmethod
from typing import List, Optional
from django_app.domain.stock_event import StockEvent


class StockEventRepository(ABC):
    @abstractmethod
    def create(self, data: dict) -> StockEvent:
        pass
    
    @abstractmethod
    def get_by_id(self, event_id: str) -> Optional[StockEvent]:
        pass
    
    @abstractmethod
    def list_events(
        self, 
        page: int, 
        page_size: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> tuple[List[StockEvent], int]:
        pass
    
    @abstractmethod
    def update(self, event_id: str, data: dict) -> Optional[StockEvent]:
        pass
    
    @abstractmethod
    def delete(self, event_id: str) -> bool:
        pass
    
    @abstractmethod
    def get_upcoming_events(self, days: int = 30) -> List[StockEvent]:
        pass
