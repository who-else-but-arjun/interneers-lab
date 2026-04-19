from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt


model = SentenceTransformer('all-MiniLM-L6-v2')


products = [
    {"name": "Lego Castle", "description": "A medieval castle building set with knights and horses"},
    {"name": "Wooden Blocks", "description": "Classic wooden building blocks for creative construction"},
    {"name": "Action Figure", "description": "Superhero action figure with movable joints and accessories"}
]


print("=" * 60)
print("TASK 2: MANUAL SIMILARITY CALCULATION")
print("=" * 60)


texts = [f"{p['name']} {p['description']}" for p in products]
print("\nProduct Texts:")
for i, text in enumerate(texts):
    print(f"  {i+1}. {text}")


print("\n" + "-" * 60)
print("Step 2a: Generating Embeddings (384 dimensions)")
print("-" * 60)

embeddings = []
for i, text in enumerate(texts):
    embedding = model.encode(text, convert_to_numpy=True)
    embeddings.append(embedding)
    print(f"\nProduct {i+1}: {products[i]['name']}")
    print(f"  Embedding shape: {embedding.shape}")
    print(f"  First 10 values: {embedding[:10]}")
    print(f"  Embedding norm: {np.linalg.norm(embedding):.4f}")


print("\n" + "-" * 60)
print("Step 2b: MANUAL Cosine Similarity Calculation")
print("-" * 60)

def manual_cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    print(f"  Dot product: {dot_product:.6f}")
    print(f"  Norm1: {norm1:.6f}")
    print(f"  Norm2: {norm2:.6f}")
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    return similarity


pairs = [
    (0, 1, "Lego Castle", "Wooden Blocks"),
    (0, 2, "Lego Castle", "Action Figure"),
    (1, 2, "Wooden Blocks", "Action Figure")
]

similarities = {}
print("\nCosine Similarities:")
for i, j, name1, name2 in pairs:
    print(f"\n{name1} vs {name2}:")
    sim = manual_cosine_similarity(embeddings[i], embeddings[j])
    similarities[(i, j)] = sim
    print(f"  Cosine Similarity: {sim:.6f} ({sim*100:.2f}%)")


print("\n" + "-" * 60)
print("Step 2c: PCA Visualization (384D → 2D)")
print("-" * 60)

embeddings_matrix = np.array(embeddings)
pca = PCA(n_components=2)
embeddings_2d = pca.fit_transform(embeddings_matrix)

print(f"\nExplained variance ratio: {pca.explained_variance_ratio_}")
print(f"Total variance preserved: {sum(pca.explained_variance_ratio_)*100:.2f}%")

print("\n2D Coordinates:")
for i, product in enumerate(products):
    print(f"  {product['name']}: ({embeddings_2d[i, 0]:.4f}, {embeddings_2d[i, 1]:.4f})")


plt.figure(figsize=(10, 8))
colors = ['#5c2145', '#8b3a5c', '#2d5a4a']
for i, product in enumerate(products):
    plt.scatter(embeddings_2d[i, 0], embeddings_2d[i, 1], 
                c=colors[i], s=300, alpha=0.7, edgecolors='white', linewidth=2)
    plt.annotate(product['name'], 
                 (embeddings_2d[i, 0], embeddings_2d[i, 1]),
                 xytext=(10, 10), textcoords='offset points',
                 fontsize=12, fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

lego_wooden_dist = np.linalg.norm(embeddings_2d[0] - embeddings_2d[1])
lego_action_dist = np.linalg.norm(embeddings_2d[0] - embeddings_2d[2])

plt.arrow(embeddings_2d[0, 0], embeddings_2d[0, 1],
          embeddings_2d[1, 0] - embeddings_2d[0, 0],
          embeddings_2d[1, 1] - embeddings_2d[0, 1],
          head_width=0.05, head_length=0.05, fc='gray', ec='gray', alpha=0.5, linestyle='--')
plt.arrow(embeddings_2d[0, 0], embeddings_2d[0, 1],
          embeddings_2d[2, 0] - embeddings_2d[0, 0],
          embeddings_2d[2, 1] - embeddings_2d[0, 1],
          head_width=0.05, head_length=0.05, fc='gray', ec='gray', alpha=0.5, linestyle=':')

plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)', fontsize=12)
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)', fontsize=12)
plt.title('Product Embeddings in 2D (PCA)\nSemantic Similarity Visualization', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('pca_visualization.png', dpi=150, bbox_inches='tight')
print("\nPlot saved as 'pca_visualization.png'")


print("\n" + "=" * 60)
print("Step 2d: ANALYSIS - Why is Lego closer to Wooden Blocks?")
print("=" * 60)

lego_wooden_sim = similarities[(0, 1)]
lego_action_sim = similarities[(0, 2)]

print(f"\nSimilarity Scores:")
print(f"  Lego Castle ↔ Wooden Blocks: {lego_wooden_sim:.4f} ({lego_wooden_sim*100:.2f}%)")
print(f"  Lego Castle ↔ Action Figure: {lego_action_sim:.4f} ({lego_action_sim*100:.2f}%)")
print(f"\nDifference: {abs(lego_wooden_sim - lego_action_sim)*100:.2f} percentage points")