from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any, Tuple
import json
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt


class SemanticSearchEngine:
    _instance = None
    
    def __new__(cls, model_name='all-MiniLM-L6-v2'):
        if cls._instance is None:
            cls._instance = super(SemanticSearchEngine, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.model_name = model_name
            cls._instance.product_embeddings = {}
            cls._instance.products = []
        return cls._instance
    
    def load_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def get_embedding(self, text: str) -> np.ndarray:
        model = self.load_model()
        return model.encode(text, convert_to_numpy=True)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def generate_product_text(self, product: Dict[str, Any]) -> str:
        return f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')} {product.get('brand', '')}"
    
    def index_products(self, products: List[Dict[str, Any]]):
        self.products = products
        self.product_embeddings = {}
        model = self.load_model()
        
        for product in products:
            text = self.generate_product_text(product)
            embedding = model.encode(text, convert_to_numpy=True)
            self.product_embeddings[product.get('id', str(hash(text)))] = embedding
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not self.products:
            return []
        
        query_embedding = self.get_embedding(query)
        
        results = []
        for product in self.products:
            product_id = product.get('id', str(hash(self.generate_product_text(product))))
            if product_id in self.product_embeddings:
                similarity = self.compute_similarity(query_embedding, self.product_embeddings[product_id])
                results.append((product, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def find_similar_products(self, product_id: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if product_id not in self.product_embeddings:
            return []
        
        target_embedding = self.product_embeddings[product_id]
        target_product = None
        for p in self.products:
            if p.get('id') == product_id:
                target_product = p
                break
        
        results = []
        for product in self.products:
            pid = product.get('id', str(hash(self.generate_product_text(product))))
            if pid != product_id and pid in self.product_embeddings:
                similarity = self.compute_similarity(target_embedding, self.product_embeddings[pid])
                results.append((product, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


semantic_search = SemanticSearchEngine()
