from abc import ABC, abstractmethod
from typing import Optional
from django_app.domain.product import Product


class ProductRepository(ABC):
    @abstractmethod
    def create(self, data: dict) -> Product:
        pass

    @abstractmethod
    def find_by_identity(self, name: str, brand: str, category: str) -> Optional[Product]:
        """
        Find a product that should be considered the same logical item for upserts,
        typically by (name, brand, optional category).
        """
        pass

    @abstractmethod
    def get_by_id(self, product_id: str) -> Optional[Product]:
        pass

    @abstractmethod
    def list_products(
        self, page: int, page_size: int, category_ids: list[str] | None = None
    ) -> tuple[list[Product], int]:
        pass

    @abstractmethod
    def update(self, product_id: str, data: dict) -> Optional[Product]:
        pass

    @abstractmethod
    def delete(self, product_id: str) -> bool:
        pass
