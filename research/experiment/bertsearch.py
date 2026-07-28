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
    {"id": 4, "title": "Spicy Peanut Noodles", "ingredients": "ramen noodles, peanut butter, soy sauce, chili oil, green onions"},
    {"id": 5, "title": "Avocado Burrata", "ingredients": "Apricot agrodolce, arugula, grilled bread, olive oil, burrata cheese, Avocado, balsamic glaze, salt, pepper"},
    {"id": 6, "title": "Roasted Nut Sauce Salad", "ingredients": "mixed greens, roasted nuts, vinaigrette, roasted nut sauce, Avocado, balsamic glaze, salt, pepper"},
    {"id": 7, "title": "Orange Flavor Beef", "ingredients": "Crispy chunks of tender beef on vegetables tossed in an orange flavored spicy hot sauce."},
    {"id": 8, "title": "Spicy Roasted Vegetables", "ingredients": "A medley of vegetables roasted with a spicy seasoning blend."},
    {"id": 9, "title": "Kids hamburger", "ingredients": "Beef burger with lettuce, tomatoes, and fries."},
    {"id": 10, "title": "Artisan focaccia sandwich", "ingredients": "breaded and pan-fried cutlet, fresh mozzarella, roasted peppers, arugula, balsamic glaze, and a side of mixed greens."},
    {"id": 11, "title": "Grilled Chicken Caesar Salad", "ingredients": "grilled chicken breast, romaine lettuce, parmesan cheese, croutons, Caesar dressing"},
    {"id": 12, "title": "Cantina Chicken Burger", "ingredients": "Pollo asado chicken, pepper jack cheese, avocado, onions, tomato and mayo on a bun. Comes with fries."},
    {"id": 13, "title": "Curry Chicken", "ingredients": "Tender chicken pieces simmered in a rich and flavorful curry sauce with aromatic spices."},

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
# past queries beef burger, vegetarian salad
# Take query from argument or use default
query = "roasted nut sauce salad"  # Default query if none provided
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])  # Join all command line arguments as the query

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

