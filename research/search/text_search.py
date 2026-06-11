"""
Baseline text search — simple substring matching across menu items.

Usage:
    python text_search.py seafood
    python text_search.py spicy pasta

Limitation: only matches if query words appear literally in name/description.
'seafood italian' will NOT find CajunPasta (clams, salmon, cod) because
neither word appears in the text. That is the problem semantic search solves.
"""
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parents[2] / "data"


def load_data() -> tuple[dict, dict]:
    with open(DATA_DIR / "restaurants.json") as f:
        restaurants = {r["id"]: r for r in json.load(f)}
    with open(DATA_DIR / "menus.json") as f:
        menus = json.load(f)
    return restaurants, menus


def search(query: str, restaurants: dict, menus: dict) -> list[dict]:
    terms = query.lower().split()
    results = []
    for restaurant_id, items in menus.items():
        for item in items:
            text = f"{item['name']} {item['description']}".lower()
            if all(term in text for term in terms):
                results.append({
                    "restaurant": restaurants[restaurant_id]["name"],
                    "item": item["name"],
                    "description": item["description"],
                    "price": item["price"],
                })
    return results


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python text_search.py <query terms>")
        sys.exit(1)

    restaurants, menus = load_data()
    results = search(query, restaurants, menus)

    print(f"Query: '{query}'  —  {len(results)} match(es)\n")
    for r in results:
        print(f"  {r['restaurant']} | {r['item']}  ${r['price']:.2f}")
        print(f"  {r['description']}")
        print()
