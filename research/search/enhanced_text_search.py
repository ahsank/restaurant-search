"""
Enhanced text search — improves recall over the substring baseline by scoring
items across multiple match tiers and including restaurant/menu context.

Scoring tiers (per query term):
  - Term in item name         → weight 4
  - Term in item description  → weight 2
  - Term in context fields    → weight 1
    (category, menu type, dietary, price_raw, restaurant name, restaurant cuisine, restaurant description)

Items are only returned when ALL mandatory query terms match across any tier combined.
Standard English stop words (e.g. 'with', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'by', 'a', 'an', 'the')
are filtered from mandatory matching, and basic singular/plural stemming is supported so inflections
(e.g. 'dishes' ↔ 'dish', 'tacos' ↔ 'taco') match their base forms.

Bonuses:
  - All query terms found in name alone  → +10
  - Normalized query == normalized name  → score 100 (exact match)

Filtered mode (filter_restaurant_ctx=True):
  Before matching a query term against restaurant-level context (cuisine,
  restaurant description), check whether the term already appears anywhere in
  that restaurant's menu (item names, descriptions, categories, menu types, dietary, price).
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

STOP_WORDS = {
    "a", "an", "the",
    "and", "or", "&",
    "with", "in", "on", "at", "to", "for", "of", "by", "from",
    "as", "into", "over", "after", "before", "between", "under", "about", "through",
    "is", "are", "was", "were", "be", "been", "being",
    "it", "its", "that", "this", "these", "those",
}


def normalize(text: str) -> str:
    """Lowercase and strip combining diacritics (à → a, é → e, etc.)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def term_variants(term: str) -> set[str]:
    """Return the term itself plus basic singular/plural variants."""
    variants = {term}
    # Plural -> singular
    if len(term) > 3:
        if term.endswith("ies") and len(term) > 4:
            variants.add(term[:-3] + "y")  # berries -> berry, fries -> fry
            variants.add(term[:-1])        # cookies -> cookie
        elif term.endswith("ves") and len(term) > 4:
            variants.add(term[:-3] + "f")   # leaves -> leaf, loaves -> loaf
            variants.add(term[:-3] + "fe")  # knives -> knife
        elif term.endswith("es") and len(term) > 3:
            if term.endswith(("shes", "ches", "sses", "xes", "zes")):
                variants.add(term[:-2])     # dishes -> dish, sandwiches -> sandwich, glasses -> glass
            elif term.endswith("oes"):
                variants.add(term[:-2])     # tomatoes -> tomato, potatoes -> potato
                variants.add(term[:-1])
            else:
                variants.add(term[:-1])     # plates -> plate, casseroles -> casserole
                variants.add(term[:-2])
        elif term.endswith("s") and not term.endswith(("ss", "us", "is")):
            variants.add(term[:-1])         # tacos -> taco, burgers -> burger, salads -> salad

    # Singular -> plural
    if len(term) > 2 and (not term.endswith("s") or term.endswith("ss")):
        if term.endswith("y") and len(term) >= 3 and term[-2] not in "aeiou":
            variants.add(term[:-1] + "ies")  # fry -> fries, berry -> berries, curry -> curries
        elif term.endswith(("sh", "ch", "ss", "x", "z")):
            variants.add(term + "es")        # dish -> dishes, sandwich -> sandwiches, glass -> glasses
        elif term.endswith("f") and len(term) > 3:
            variants.add(term[:-1] + "ves")  # loaf -> loaves, leaf -> leaves
            variants.add(term + "s")
        elif term.endswith("fe") and len(term) > 3:
            variants.add(term[:-2] + "ves")  # knife -> knives
            variants.add(term + "s")
        elif term.endswith("o") and len(term) > 3:
            variants.add(term + "es")        # tomato -> tomatoes, potato -> potatoes, taco -> tacos
            variants.add(term + "s")
        else:
            variants.add(term + "s")

    return {v for v in variants if v}


def build_menu_vocab(menus: dict) -> dict[str, set[str]]:
    """
    Per-restaurant set of all words appearing in item names, descriptions,
    categories, menu types, dietary annotations, and price. Used to suppress
    restaurant-level context matching for terms already findable via item-level matching.
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
                item.get("dietary") or "",
                item.get("price_raw") or "",
            ):
                for token in normalize(field).split():
                    t = token.strip(".,;:!?\"'()")
                    if t:
                        words.add(t)
                        words.update(term_variants(t))
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
    dietary = normalize(item.get("dietary") or "")
    price_raw = normalize(item.get("price_raw") or "")
    rest_dict = restaurant or {}
    rest_name = normalize(rest_dict.get("name", ""))
    cuisine = normalize(rest_dict.get("cuisine", ""))
    rest_desc = normalize(rest_dict.get("description", ""))

    if query_norm == name:
        return 100

    # Ensure stop words are filtered from mandatory matching
    terms = [t for t in query_terms if t not in STOP_WORDS] or query_terms

    name_hits = desc_hits = ctx_hits = 0
    for term in terms:
        variants = term_variants(term)
        if any(v in name for v in variants):
            name_hits += 1
        elif any(v in desc for v in variants):
            desc_hits += 1
        elif any(v in category or v in menu_type or v in dietary or v in price_raw for v in variants):
            ctx_hits += 1
        elif any(v in rest_name or v in cuisine or v in rest_desc for v in variants):
            # Skip restaurant-level context if this term is already
            # findable anywhere in the menu (item-level matching handles it).
            if menu_vocab is None or any(v in rest_name for v in variants) or not any(v in menu_vocab for v in variants):
                ctx_hits += 1

    total = name_hits + desc_hits + ctx_hits
    if total < len(terms):
        return 0

    score = name_hits * 4 + desc_hits * 2 + ctx_hits * 1
    if name_hits == len(terms):
        score += 10  # all terms in item name alone
    return score


def search(
    query: str,
    restaurants: dict,
    menus: dict,
    filter_restaurant_ctx: bool = False,
) -> list[dict]:
    query_norm = normalize(query)
    raw_terms = [t.strip(".,;:!?\"'()") for t in query_norm.split()]
    raw_terms = [t for t in raw_terms if t]
    query_terms = [t for t in raw_terms if t not in STOP_WORDS]
    if not query_terms:
        query_terms = raw_terms
    all_vocab = build_menu_vocab(menus) if filter_restaurant_ctx else {}
    scored: list[tuple[int, dict]] = []

    for restaurant_id, items in menus.items():
        restaurant = restaurants.get(restaurant_id, {})
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
                    "dietary": item.get("dietary", ""),
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
    restaurants, menus = load_data(judged_restaurant_ids())
    results = search(query, restaurants, menus, filter_restaurant_ctx=args.filtered)

    mode = "filtered" if args.filtered else "unfiltered"
    print(f"Query: '{query}'  [{mode}]  —  {len(results)} match(es)\n")
    for r in results:
        price_str = f"${r['price']:.2f}" if r["price"] is not None else (r["price_raw"] or "N/A")
        dietary_str = f" ({r['dietary']})" if r.get("dietary") else ""
        print(
            f"  [{r['score']:>3}] {r['restaurant']} | {r['item']}  {price_str}"
            f"  [{r['category']} · {r['menu_type']}]{dietary_str}"
        )
        if r["description"]:
            print(f"       {r['description']}")
        print()
