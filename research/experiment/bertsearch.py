import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# 1. Load a model optimized for sentence/phrase embeddings (based on BERT architecture)
# 'all-MiniLM-L6-v2' is fast, lightweight, and excellent for semantic search
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Define your recipe dataset
recipes = [
    {"id": 0, "title": "Avocado Toast", "ingredients": "toasted bread, smashed avocado, salt, pepper, olive oil"},
    {"id": 1, "title": "Crunchy Almond Salad", "ingredients": "mixed greens, sliced cucumber, toasted almonds, vinaigrette"},
    {"id": 2, "title": "Peanut Butter Shake", "ingredients": "creamy peanut butter, frozen banana, milk, honey"},
    {"id": 3, "title": "Garlic Bread", "ingredients": "baguette, butter, minced garlic, parsley, salt"},
    {"id": 4, "title": "Spicy Peanut Noodles", "ingredients": "ramen noodles, peanut butter, soy sauce, chili oil, green onions"}
]

# Create searchable strings combining titles and ingredients
recipe_texts = [f"{r['title']}: {r['ingredients']}" for r in recipes]

# 3. Convert all recipes into vectors (Dense Embeddings)
# This will output a matrix of shape [num_recipes, 384]
recipe_embeddings = model.encode(recipe_texts, convert_to_numpy=True)

# 4. Build a FAISS Index for fast vector similarity math
vector_dimension = recipe_embeddings.shape[1]
# IndexFlatIP uses Inner Product (Cosine Similarity for normalized vectors)
index = faiss.IndexFlatIP(vector_dimension) 

# Normalize vectors so that Inner Product calculation matches Cosine Similarity exactly
faiss.normalize_L2(recipe_embeddings)
index.add(recipe_embeddings)

# 5. Define your search query
# Notice we are searching for "roasted" and "sauce", words not explicitly in the dataset text
query = "salad with a roasted nut sauce" 

# Convert query to a vector and normalize it
query_embedding = model.encode([query], convert_to_numpy=True)
faiss.normalize_L2(query_embedding)

# 6. Search the index for the top 2 closest matches
k = 2  # Number of nearest neighbors to find
similarities, indices = index.search(query_embedding, k)

# 7. Print the results
print(f"Search Query: '{query}'\n")
print("Top Matching Recipes:")
for score, idx in zip(similarities[0], indices[0]):
    matched_recipe = recipes[idx]
    print(f"- {matched_recipe['title']} (Confidence Score: {score:.4f})")
    print(f"  Ingredients: {matched_recipe['ingredients']}\n")

