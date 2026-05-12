from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer


SEARCH_TEST_CASES = [
    {
        "query": "construction toys",
        "relevant_products": ["lego_castle_001", "lego_city_002", "wooden_blocks_003"],
        "irrelevant_products": ["teddy_bear_010", "action_figure_015", "doll_house_020"]
    },
    {
        "query": "gifts for toddlers",
        "relevant_products": ["soft_blocks_004", "plush_toy_005", "baby_rattle_006"],
        "irrelevant_products": ["puzzle_1000pc_020", "teen_board_game_025", "lego_technic_030"]
    },
    {
        "query": "educational toys",
        "relevant_products": ["math_learning_kit_001", "science_set_002", "alphabet_blocks_003"],
        "irrelevant_products": ["water_gun_010", "fidget_spinner_015", "stuffed_animal_020"]
    },
    {
        "query": "outdoor play",
        "relevant_products": ["swing_set_001", "sandbox_002", "water_slide_003"],
        "irrelevant_products": ["board_game_010", "lego_set_015", "puzzle_020"]
    },
    {
        "query": "creative building",
        "relevant_products": ["lego_classic_001", "wooden_blocks_002", "magnetic_tiles_003"],
        "irrelevant_products": ["action_figure_010", "rc_car_015", "doll_020"]
    }
]


class SemanticSearchService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.products = []
        self.embeddings = {}
        self.model_name = model_name
    
    def generate_product_text(self, product: Dict[str, Any]) -> str:
        return f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')} {product.get('brand', '')}"
    
    def compute_cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def index_products(self, products: List[Dict[str, Any]]):
        self.products = products
        self.embeddings = {}
        for product in products:
            text = self.generate_product_text(product)
            embedding = self.model.encode(text, convert_to_numpy=True)
            product_id = product.get('id', str(hash(text)))
            self.embeddings[product_id] = embedding
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not self.products:
            return []
        
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        results = []
        for product in self.products:
            product_id = product.get('id', str(hash(self.generate_product_text(product))))
            if product_id in self.embeddings:
                similarity = self.compute_cosine_similarity(query_embedding, self.embeddings[product_id])
                results.append((product, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def evaluate_search(self, test_cases: List[Dict] = None) -> Dict[str, Any]:
        if test_cases is None:
            test_cases = SEARCH_TEST_CASES
        
        results = {
            "test_cases": [],
            "overall_precision": 0.0,
            "overall_recall": 0.0,
            "overall_f1": 0.0,
            "average_top_k_accuracy": 0.0
        }
        
        total_precision = 0.0
        total_recall = 0.0
        total_top_k_acc = 0.0
        
        for test_case in test_cases:
            query = test_case["query"]
            relevant = set(test_case["relevant_products"])
            irrelevant = set(test_case["irrelevant_products"])
            
            search_results = self.search(query, top_k=10)
            returned_ids = [r[0].get('id', '') for r in search_results]
            
            true_positives = len(set(returned_ids) & relevant)
            false_positives = len(set(returned_ids) & irrelevant)
            false_negatives = len(relevant - set(returned_ids))
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            top_k_acc = 0.0
            for i, (product, score) in enumerate(search_results[:5]):
                if product.get('id', '') in relevant:
                    top_k_acc += 1
            top_k_acc /= 5
            
            total_precision += precision
            total_recall += recall
            total_top_k_acc += top_k_acc
            
            results["test_cases"].append({
                "query": query,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "top_5_accuracy": top_k_acc,
                "results_count": len(search_results)
            })
        
        num_cases = len(test_cases)
        results["overall_precision"] = total_precision / num_cases
        results["overall_recall"] = total_recall / num_cases
        results["overall_f1"] = 2 * (results["overall_precision"] * results["overall_recall"]) / (results["overall_precision"] + results["overall_recall"]) if (results["overall_precision"] + results["overall_recall"]) > 0 else 0.0
        results["average_top_k_accuracy"] = total_top_k_acc / num_cases
        
        return results


def semantic_search_demo():
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
        {"id": "stuffed_animal_020", "name": "Stuffed Elephant", "description": "Cute plush elephant", "category": "Plush Toys", "brand": "Wild Republic"}
    ]
    
    service = SemanticSearchService()
    service.index_products(sample_products)
    
    print("=" * 60)
    print("TASK 3: SEMANTIC SEARCH")
    print("=" * 60)
    
    queries = [
        "construction toys",
        "building blocks for kids",
        "educational learning toys",
        "soft toys for babies"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        results = service.search(query, top_k=5)
        for i, (product, score) in enumerate(results):
            print(f"  {i+1}. {product['name']} (score: {score:.4f})")
            print(f"     {product['description'][:60]}...")
    
    print("\n" + "=" * 60)
    print("TASK 4: EVALUATION FRAMEWORK")
    print("=" * 60)
    
    eval_results = service.evaluate_search(SEARCH_TEST_CASES)
    
    print("\nTest Case Results:")
    print("-" * 60)
    for case in eval_results["test_cases"]:
        print(f"\nQuery: '{case['query']}'")
        print(f"  Precision: {case['precision']:.2f}")
        print(f"  Recall: {case['recall']:.2f}")
        print(f"  F1 Score: {case['f1_score']:.2f}")
        print(f"  Top-5 Accuracy: {case['top_5_accuracy']:.2f}")
    
    print("\n" + "-" * 60)
    print("OVERALL METRICS:")
    print(f"  Average Precision: {eval_results['overall_precision']:.3f}")
    print(f"  Average Recall: {eval_results['overall_recall']:.3f}")
    print(f"  Average F1 Score: {eval_results['overall_f1']:.3f}")
    print(f"  Top-K Accuracy: {eval_results['average_top_k_accuracy']:.3f}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    semantic_search_demo()
