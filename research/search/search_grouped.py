"""
Group a search engine's flat results by restaurant: top N restaurants, top K
items each. This is the shape a web search UI would actually display — the
grouping logic here (group_results) has no CLI/print dependencies, so a future
web backend can import it directly instead of reimplementing it.

Usage:
    python search_grouped.py --engine colbert --top-restaurants 10 --top-items 3 creamy pasta
    python search_grouped.py --engine soft_bm25 --vectors models/numberbatch-en.txt seafood
    python search_grouped.py --engine text --benchmark-only burger
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args
from lib.ranking import restaurant_scores


def group_results(results: list[dict], n_restaurants: int, k_items: int) -> list[dict]:
    """
    results: flat, best-first list of item dicts, each with at least
        "restaurant_id" and "restaurant" (display name) — the shape every
        engine in engines.py returns.

    Restaurant order is derived from each item's *rank position* in results,
    not a raw engine score: scores aren't guaranteed to exist (text_search
    returns none) and aren't comparable across engines anyway (ColBERT ~19,
    soft_bm25 ~5, SBERT cosine ~0-1). Rank position is universal and directly
    reflects "how highly did the engine rank this restaurant's best dishes."

    Returns: [{"restaurant_id", "restaurant", "score", "items": [...]}, ...],
        top n_restaurants, each with up to k_items — already that restaurant's
        own best items, since results is best-first.
    """
    item_values = [(r["restaurant_id"], 1.0 / (i + 1)) for i, r in enumerate(results)]
    ranked = restaurant_scores(item_values, k_items)

    by_restaurant: dict[str, list[dict]] = {}
    for r in results:
        by_restaurant.setdefault(r["restaurant_id"], []).append(r)

    grouped = []
    for rid, score, _ in ranked[:n_restaurants]:
        items = by_restaurant[rid][:k_items]
        grouped.append({
            "restaurant_id": rid,
            "restaurant": items[0]["restaurant"],
            "score": score,
            "items": items,
        })
    return grouped


if __name__ == "__main__":
    import engines

    parser = engines.build_arg_parser(
        "Search grouped by restaurant — top N restaurants, top K dishes each",
        parents=[restaurant_scope_cli_args()],
    )
    parser.add_argument("--top-restaurants", type=int, default=3,
                        help="How many restaurants to show (default 3 — raise once the "
                             "restaurant corpus grows past a handful)")
    parser.add_argument("--top-items", type=int, default=3,
                        help="How many dishes to show per restaurant (default 3)")
    parser.add_argument("terms", nargs="+", help="Query words")
    args = parser.parse_args()

    query = " ".join(args.terms)

    print("Loading menus...", end=" ", flush=True)
    restaurants, menus = load_data(judged_restaurant_ids() if args.benchmark_only else None)
    print(f"{sum(len(v) for v in menus.values())} items"
          + (" (benchmark subset)" if args.benchmark_only else ""))

    search_fn = engines.build_search_fn(args, restaurants, menus)

    print(f"\nQuery: '{query}'\n")
    results = search_fn(query)
    grouped = group_results(results, args.top_restaurants, args.top_items)

    if not grouped:
        print("No results.")
    for g in grouped:
        print(f"== {g['restaurant']}  (score={g['score']:.4f}) ==")
        for item in g["items"]:
            price_str = (
                f"${item['price']:.2f}" if item.get("price") is not None
                else item.get("price_raw") or "N/A"
            )
            print(f"  {item['name']}  {price_str}  [{item.get('category')} · {item.get('menu_type')}]")
            if item.get("description"):
                print(f"    {item['description']}")
        print()
