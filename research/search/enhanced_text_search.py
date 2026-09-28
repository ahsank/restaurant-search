"""
Enhanced text search — improves recall over the substring baseline by scoring
items across multiple match tiers and including restaurant/menu context.

Scoring tiers (per query term):
  - Term in item name         → weight 4
  - Term in item description  → weight 2
  - Term in context fields    → weight 1
    (category, menu type, restaurant cuisine, restaurant description)

Items are only returned when ALL query terms match across any tier combined.

Bonuses:
  - All query terms found in name alone  → +10
  - Normalized query == normalized name  → score 100 (exact match)

Filtered mode (filter_restaurant_ctx=True):
  Before matching a query term against restaurant-level context (cuisine,
  restaurant description), check whether the term already appears anywhere in
  that restaurant's menu (item names, descriptions, categories, menu types).
  If it does, skip the restaurant-level match — item-level matching handles it.
  This prevents a label like "pasta" in `cuisine: italian, pasta, sandwiches`
  from surfacing every item in the restaurant for a "pasta" query.

Accent normalization: diacritics are stripped before comparison so that
"camarones a la diabla" matches "Camarones à la Diabla".

Results are returned sorted by score descending; items with score 0 are excluded.

Usage:
    python enhanced_text_search.py seafood
    python enhanced_text_search.py spicy pasta
    python enhanced_text_search.py --filtered pasta
"""
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args


def normalize(text: str) -> str:
    """Lowercase and strip combining diacritics (à → a, é → e, etc.)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def build_menu_vocab(menus: dict) -> dict[str, set[str]]:
    """
    Per-restaurant set of all words appearing in item names, descriptions,
    categories, and menu types. Used to suppress restaurant-level context
    matching for terms already findable via item-level matching.
    """
    vocab: dict[str, set[str]] = {}
    for restaurant_id, items in menus.items():
        words: set[str] = set()
        for item in items:
            for field in (
                item["name"],
                item["description"],
                item.get("category") or "",
                item.get("menu_type") or "",
            ):
                words.update(normalize(field).split())
        vocab[restaurant_id] = words
    return vocab


def _score_item(
    query_terms: list[str],
    query_norm: str,
    item: dict,
    restaurant: dict,
    menu_vocab: set[str] | None = None,
) -> int:
    name = normalize(item["name"])
    desc = normalize(item["description"])
    category = normalize(item.get("category") or "")
    menu_type = normalize(item.get("menu_type") or "")
    cuisine = normalize(restaurant.get("cuisine", ""))
    rest_desc = normalize(restaurant.get("description", ""))

    if query_norm == name:
        return 100

    name_hits = desc_hits = ctx_hits = 0
    for term in query_terms:
        if term in name:
            name_hits += 1
        elif term in desc:
            desc_hits += 1
        elif term in category or term in menu_type:
            ctx_hits += 1
        elif term in cuisine or term in rest_desc:
            # Skip restaurant-level context if this term is already
            # findable anywhere in the menu (item-level matching handles it).
            if menu_vocab is None or term not in menu_vocab:
                ctx_hits += 1

    total = name_hits + desc_hits + ctx_hits
    if total < len(query_terms):
        return 0

    score = name_hits * 4 + desc_hits * 2 + ctx_hits * 1
    if name_hits == len(query_terms):
        score += 10  # all terms in item name alone
    return score


def search(
    query: str,
    restaurants: dict,
    menus: dict,
    filter_restaurant_ctx: bool = False,
) -> list[dict]:
    query_norm = normalize(query)
    query_terms = query_norm.split()
    all_vocab = build_menu_vocab(menus) if filter_restaurant_ctx else {}
    scored: list[tuple[int, dict]] = []

    for restaurant_id, items in menus.items():
        restaurant = restaurants[restaurant_id]
        restaurant_name = restaurant.get("name", restaurant_id)
        menu_vocab = all_vocab.get(restaurant_id) if filter_restaurant_ctx else None
        for item in items:
            score = _score_item(query_terms, query_norm, item, restaurant, menu_vocab)
            if score > 0:
                scored.append((score, {
                    "restaurant": restaurant_name,
                    "item": item["name"],
                    "description": item["description"],
                    "price": item["price"],
                    "price_raw": item["price_raw"],
                    "category": item["category"],
                    "menu_type": item["menu_type"],
                    "score": score,
                }))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [r for _, r in scored]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[restaurant_scope_cli_args()])
    parser.add_argument("--filtered", action="store_true",
                        help="Filter restaurant context by menu vocabulary")
    parser.add_argument("terms", nargs="+")
    args = parser.parse_args()

    query = " ".join(args.terms)
    restaurants, menus = load_data(judged_restaurant_ids() if args.benchmark_only else None)
    results = search(query, restaurants, menus, filter_restaurant_ctx=args.filtered)

    mode = "filtered" if args.filtered else "unfiltered"
    print(f"Query: '{query}'  [{mode}]  —  {len(results)} match(es)\n")
    for r in results:
        price_str = f"${r['price']:.2f}" if r["price"] is not None else (r["price_raw"] or "N/A")
        print(
            f"  [{r['score']:>3}] {r['restaurant']} | {r['item']}  {price_str}"
            f"  [{r['category']} · {r['menu_type']}]"
        )
        if r["description"]:
            print(f"       {r['description']}")
        print()
