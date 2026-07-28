"""
Toy version of sbert_search.py using the same hardcoded dataset and query
as bertsearch.py — run both side by side to compare results.

bertsearch.py  uses FAISS IndexFlatIP for similarity search.
menu_search.py uses a plain numpy dot-product scan (same math, no FAISS).

Both use all-MiniLM-L6-v2 and cosine similarity on unit-normalised vectors,
so results should be identical. Any difference points to a real algorithmic
distinction worth investigating.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

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

# Encode items — same text format as bertsearch.py
item_texts = [f"{r['title']}: {r['ingredients']}" for r in recipes]
item_vecs = model.encode(item_texts, normalize_embeddings=True, convert_to_numpy=True)

query = "grilled chicken"
query_vec = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)

# Cosine similarity via dot product (vectors are already unit-normalised)
scores = item_vecs @ query_vec

k = 2
top_indices = np.argsort(scores)[::-1][:k]

print(f"Search Query: '{query}'\n")
print("Top Matching Recipes:")
for idx in top_indices:
    r = recipes[idx]
    print(f"- {r['title']} (Confidence Score: {scores[idx]:.4f})")
    print(f"  Ingredients: {r['ingredients']}\n")
