from sentence_transformers import SentenceTransformer
import numpy as np
import time
from typing import List, Dict, Any, Tuple


sample_products = [
    {"id": "lego_castle_001", "name": "Lego Castle", "description": "A medieval castle building set with knights and horses", "category": "Building Toys", "brand": "Lego"},
    {"id": "lego_city_002", "name": "Lego City", "description": "City building blocks with vehicles and minifigures", "category": "Building Toys", "brand": "Lego"},
    {"id": "wooden_blocks_003", "name": "Wooden Blocks", "description": "Classic wooden building blocks for creative construction", "category": "Building Toys", "brand": "Melissa & Doug"},
    {"id": "soft_blocks_004", "name": "Soft Blocks", "description": "Soft foam blocks safe for toddlers", "category": "Baby Toys", "brand": "Fisher-Price"},
    {"id": "plush_toy_005", "name": "Plush Teddy Bear", "description": "Soft cuddly teddy bear for toddlers", "category": "Plush Toys", "brand": "Gund"},
    {"id": "baby_rattle_006", "name": "Baby Rattle", "description": "Colorful rattle for infants", "category": "Baby Toys", "brand": "Fisher-Price"},
    {"id": "teddy_bear_010", "name": "Giant Teddy Bear", "description": "Large stuffed teddy bear for hugging", "category": "Plush Toys", "brand": "Gund"},
    {"id": "action_figure_015", "name": "Superhero Action Figure", "description": "Poseable superhero figure with accessories", "category": "Action Figures", "brand": "Marvel"},
    {"id": "doll_house_020", "name": "Doll House", "description": "Victorian style doll house with furniture", "category": "Dolls", "brand": "Barbie"},
    {"id": "math_learning_kit_001", "name": "Math Learning Kit", "description": "Educational math toys for kids learning numbers", "category": "Educational", "brand": "Learning Resources"},
    {"id": "science_set_002", "name": "Science Experiment Set", "description": "Chemistry set for young scientists", "category": "Educational", "brand": "Thames & Kosmos"},
    {"id": "alphabet_blocks_003", "name": "Alphabet Blocks", "description": "Wooden blocks with letters for learning", "category": "Educational", "brand": "Melissa & Doug"},
    {"id": "water_gun_010", "name": "Super Soaker", "description": "High pressure water gun for summer fun", "category": "Outdoor", "brand": "Nerf"},
    {"id": "fidget_spinner_015", "name": "Fidget Spinner", "description": "Stress relief toy for focus", "category": "Fidgets", "brand": "Spin Master"},
    {"id": "stuffed_animal_020", "name": "Stuffed Elephant", "description": "Cute plush elephant", "category": "Plush Toys", "brand": "Wild Republic"},
    {"id": "trampoline_001", "name": "Kids Trampoline", "description": "Small indoor trampoline for active play", "category": "Outdoor", "brand": "Little Tikes"},
    {"id": "play_kitchen_002", "name": "Play Kitchen", "description": "Toy kitchen set with utensils and sounds", "category": "Pretend Play", "brand": "Step2"},
    {"id": "doctor_kit_003", "name": "Doctor Kit", "description": "Toy medical kit for pretend doctor play", "category": "Pretend Play", "brand": "Fisher-Price"},
    {"id": "rc_car_004", "name": "RC Race Car", "description": "Remote controlled racing car", "category": "Vehicles", "brand": "Hot Wheels"},
    {"id": "train_set_005", "name": "Wooden Train Set", "description": "Classic wooden train track with engines", "category": "Vehicles", "brand": "Brio"}
]


test_query = "toys for 5-year-olds"


def generate_product_text(product: Dict[str, Any]) -> str:
    return f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')} {product.get('brand', '')}"


def compute_cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


class ModelComparator:
    def __init__(self, model_name: str):
        print(f"\nLoading {model_name}...")
        start_time = time.time()
        self.model = SentenceTransformer(model_name)
        self.load_time = time.time() - start_time
        self.model_name = model_name
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"  Loaded in {self.load_time:.2f}s")
        print(f"  Embedding dimension: {self.dimension}")
    
    def index_products(self, products: List[Dict[str, Any]]):
        self.products = products
        texts = [generate_product_text(p) for p in products]
        
        start_time = time.time()
        self.embeddings = self.model.encode(texts, convert_to_numpy=True)
        self.index_time = time.time() - start_time
        
        print(f"  Indexed {len(products)} products in {self.index_time:.3f}s")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        start_time = time.time()
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        encode_time = time.time() - start_time
        
        results = []
        for i, product in enumerate(self.products):
            similarity = compute_cosine_similarity(query_embedding, self.embeddings[i])
            results.append((product, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k], encode_time


def run_comparison():
    print("=" * 70)
    print("ADVANCED TASK 2: COMPARING EMBEDDING MODELS")
    print("=" * 70)
    
    print("\n" + "-" * 70)
    print("Model A: all-MiniLM-L6-v2 (384 dimensions, fast)")
    print("-" * 70)
    model_a = ModelComparator('all-MiniLM-L6-v2')
    model_a.index_products(sample_products)
    results_a, encode_time_a = model_a.search(test_query, top_k=5)
    
    print("\nTop 5 results for query: 'toys for 5-year-olds'")
    for i, (product, score) in enumerate(results_a):
        print(f"  {i+1}. {product['name']} ({product['category']}) - Score: {score:.4f}")
    print(f"  Query encoding time: {encode_time_a*1000:.2f}ms")
    
    print("\n" + "-" * 70)
    print("Model B: all-mpnet-base-v2 (768 dimensions, slower)")
    print("-" * 70)
    model_b = ModelComparator('all-mpnet-base-v2')
    model_b.index_products(sample_products)
    results_b, encode_time_b = model_b.search(test_query, top_k=5)
    
    print("\nTop 5 results for query: 'toys for 5-year-olds'")
    for i, (product, score) in enumerate(results_b):
        print(f"  {i+1}. {product['name']} ({product['category']}) - Score: {score:.4f}")
    print(f"  Query encoding time: {encode_time_b*1000:.2f}ms")
    
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    print(f"\n{'Metric':<30} {'MiniLM (384D)':<20} {'MPNet (768D)':<20}")
    print("-" * 70)
    print(f"{'Model Size':<30} {'~80 MB':<20} {'~420 MB':<20}")
    print(f"{'Embedding Dimensions':<30} {model_a.dimension:<20} {model_b.dimension:<20}")
    print(f"{'Load Time':<30} {f'{model_a.load_time:.2f}s':<20} {f'{model_b.load_time:.2f}s':<20}")
    print(f"{'Indexing Time':<30} {f'{model_a.index_time*1000:.1f}ms':<20} {f'{model_b.index_time*1000:.1f}ms':<20}")
    print(f"{'Query Encode Time':<30} {f'{encode_time_a*1000:.2f}ms':<20} {f'{encode_time_b*1000:.2f}ms':<20}")


if __name__ == "__main__":
    run_comparison()
