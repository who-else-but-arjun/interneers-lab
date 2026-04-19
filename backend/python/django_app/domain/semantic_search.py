from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any, Tuple
import hashlib


class SemanticSearchEngine:
    _instance = None

    def __new__(cls, model_name='all-MiniLM-L6-v2'):
        if cls._instance is None:
            cls._instance = super(SemanticSearchEngine, cls).__new__(cls)
            cls._instance.model        = None
            cls._instance.model_name   = model_name
            cls._instance.products     = []
            cls._instance._ids         = []
            cls._instance._matrix     = None
            cls._instance._fingerprint = None
        return cls._instance

    def load_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model

    def _product_text(self, product: Dict[str, Any]) -> str:
        return (
            f"{product.get('name', '')} "
            f"{product.get('description', '')} "
            f"{product.get('category', '')} "
            f"{product.get('brand', '')}"
        )

    def _fingerprint_products(self, products: List[Dict[str, Any]]) -> str:
        key = "|".join(
            f"{p.get('id')}:{p.get('name')}:{p.get('description')}:{p.get('category')}:{p.get('brand')}"
            for p in products
        )
        return hashlib.md5(key.encode()).hexdigest()

    def index_products(self, products: List[Dict[str, Any]]):
        fp = self._fingerprint_products(products)
        if fp == self._fingerprint and self._matrix is not None:
            return

        model = self.load_model()
        texts = [self._product_text(p) for p in products]

        embeddings = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        self.products     = products
        self._ids         = [p.get('id', str(i)) for i, p in enumerate(products)]
        self._matrix      = embeddings
        self._fingerprint = fp

    def _query_vector(self, query: str) -> np.ndarray:
        model = self.load_model()
        vec = model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        return vec

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if self._matrix is None or len(self.products) == 0:
            return []

        q = self._query_vector(query)
        scores = self._matrix @ q

        top_k = min(top_k, len(scores))
        top_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        return [(self.products[i], float(scores[i])) for i in top_indices]

    def find_similar_products(self, product_id: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self._matrix is None or product_id not in self._ids:
            return []

        idx = self._ids.index(product_id)
        target_vec = self._matrix[idx]
        scores = self._matrix @ target_vec

        scores[idx] = -1.0

        top_k = min(top_k, len(scores) - 1)
        top_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        return [(self.products[i], float(scores[i])) for i in top_indices]


semantic_search = SemanticSearchEngine()