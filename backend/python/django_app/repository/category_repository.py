from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from django_app.domain.product_category import ProductCategory


class ProductCategoryRepository(ABC):
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> ProductCategory:
        pass

    @abstractmethod
    def get_by_id(self, category_id: str) -> Optional[ProductCategory]:
        pass

    @abstractmethod
    def list_all(self) -> List[ProductCategory]:
        pass

    @abstractmethod
    def update(self, category_id: str, data: Dict[str, Any]) -> Optional[ProductCategory]:
        pass

    @abstractmethod
    def delete(self, category_id: str) -> bool:
        pass
