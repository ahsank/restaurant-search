"""
Baseline text search — simple substring matching across menu items.

Usage:
    python text_search.py seafood
    python text_search.py spicy pasta

Limitation: only matches if query words appear literally in name/description.
'seafood italian' will NOT find CajunPasta (clams, salmon, cod) because
neither word appears in the text. That is the problem semantic search solves.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args


def search(query: str, restaurants: dict, menus: dict) -> list[dict]:
    terms = query.lower().split()
    results = []
    for restaurant_id, items in menus.items():
        restaurant_name = restaurants[restaurant_id].get("name", restaurant_id)
        for item in items:
            text = f"{item['name']} {item['description']}".lower()
            if all(term in text for term in terms):
                results.append({
                    "restaurant": restaurant_name,
                    "item": item["name"],
                    "description": item["description"],
                    "price": item["price"],
                    "price_raw": item["price_raw"],
                    "category": item["category"],
                    "menu_type": item["menu_type"],
                })
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[restaurant_scope_cli_args()])
    parser.add_argument("terms", nargs="+", help="Query words")
    args = parser.parse_args()

    query = " ".join(args.terms)
    restaurants, menus = load_data(judged_restaurant_ids() if args.benchmark_only else None)
    results = search(query, restaurants, menus)

    print(f"Query: '{query}'  —  {len(results)} match(es)\n")
    for r in results:
        price_str = f"${r['price']:.2f}" if r["price"] is not None else (r["price_raw"] or "N/A")
        print(f"  {r['restaurant']} | {r['item']}  {price_str}  [{r['category']} · {r['menu_type']}]")
        if r["description"]:
            print(f"  {r['description']}")
        print()
