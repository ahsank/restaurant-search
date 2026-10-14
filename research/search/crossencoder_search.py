"""
Approach 6: cross-encoder search — exhaustive, not a reranker (yet).

A cross-encoder reads query and item together in one forward pass, so it
can't precompute item vectors the way sbert_search.py does. The intended
production use is to rerank a bi-encoder/ColBERT top-K (see Approach 6 in
research/APPROACHES.md), but while speed isn't the focus this scores *every*
menu item against the query. That measures the cross-encoder's own ranking
quality without it being capped by a first-stage retriever's recall.

Cost: one forward pass per item per query. Over the 7 benchmark restaurants
(~640 items) that's a few seconds per query on CPU — fine for the benchmark,
not for a web request.

Item text is restaurant name, item name, description, category, menu type,
dietary annotations, and price (matching hybrid_search.py).

Usage:
    python research/search/crossencoder_search.py seafood italian
    python research/search/crossencoder_search.py --benchmark-only spicy noodles
    python research/search/crossencoder_search.py --model cross-encoder/ms-marco-MiniLM-L6-v2 oyster

Equivalent via the shared --engine dispatcher (used by evaluate.py):
    python research/search/evaluate.py --engine crossencoder --model models/crossencoder-synthetic-plus-gapfill
"""

import sys
from pathlib import Path

from sentence_transformers.cross_encoder import CrossEncoder

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args

_ROOT = Path(__file__).parents[2]
_DEFAULT_MODEL = _ROOT / "models" / "crossencoder-synthetic-plus-gapfill"
STOCK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


def _item_text(item: dict, restaurant_name: str = "") -> str:
    """
    Build text for CrossEncoder scoring:
    restaurant name, item name, description, category, menu type, dietary annotations, and price (matches hybrid_search.py).
    """
    r_name = restaurant_name or (item.get("restaurant") if isinstance(item.get("restaurant"), str) else "") or item.get("restaurant_name", "")
    parts = []
    if r_name:
        parts.append(r_name)
    if item.get("name"):
        parts.append(item["name"])
    if item.get("description"):
        parts.append(item["description"])
    if item.get("category"):
        parts.append(item["category"])
    if item.get("menu_type"):
        parts.append(item["menu_type"])
    if item.get("dietary"):
        parts.append(item["dietary"])
    if item.get("price_raw"):
        parts.append(item["price_raw"])
    return ". ".join(p for p in parts if p)


item_text = _item_text


def build_index(menus: dict, restaurants: dict) -> list[tuple[str, dict, str]]:
    """Flatten every item into (restaurant_id, item, item_text). Nothing to encode up front."""
    return [
        (rid, item, _item_text(item, restaurants.get(rid, {}).get("name", rid) if isinstance(restaurants.get(rid), dict) else rid))
        for rid, items in menus.items()
        for item in items
    ]


def search(
    query: str,
    restaurants: dict,
    index: list[tuple[str, dict, str]],
    model: CrossEncoder,
    batch_size: int = 128,
) -> list[dict]:
    """Score (query, item_text) for every indexed item and sort best-first."""
    scores = model.predict(
        [(query, text) for _, _, text in index],
        batch_size=batch_size,
        show_progress_bar=False,
    )

    scored: list[tuple[float, dict]] = []
    for (rid, item, _), score in zip(index, scores):
        score = float(score)
        scored.append((score, {
            "restaurant":  restaurants[rid].get("name", rid),
            "item":        item["name"],
            "description": item["description"],
            "price":       item["price"],
            "price_raw":   item["price_raw"],
            "category":    item["category"],
            "menu_type":   item["menu_type"],
            "score":       round(score, 4),
        }))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [r for _, r in scored]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Cross-encoder menu search (Approach 6), scoring every item",
        parents=[restaurant_scope_cli_args()],
    )
    parser.add_argument(
        "--model", default=str(_DEFAULT_MODEL),
        help=f"Finetuned model directory or hub name (default: {_DEFAULT_MODEL}; "
             f"stock baseline: {STOCK_MODEL})",
    )
    parser.add_argument("terms", nargs="+", help="Query words")
    args = parser.parse_args()

    if args.model == str(_DEFAULT_MODEL) and not _DEFAULT_MODEL.exists():
        raise SystemExit(
            f"Model not found at '{args.model}'. Train one first:\n"
            f"  python research/train/finetune_crossencoder.py\n"
            f"or pass --model {STOCK_MODEL} for the stock checkpoint."
        )

    print(f"Loading model '{args.model}'...", end=" ", flush=True)
    model = CrossEncoder(args.model)
    print("done")

    restaurants, menus = load_data(judged_restaurant_ids() if args.benchmark_only else None)
    index = build_index(menus, restaurants)
    print(f"{len(index)} items to score")

    query = " ".join(args.terms)
    print(f"\nQuery: '{query}'\n")

    results = search(query, restaurants, index, model)

    for r in results[:20]:
        price_str = (
            f"${r['price']:.2f}" if r["price"] is not None
            else r["price_raw"] or "N/A"
        )
        print(
            f"  [{r['score']:.4f}] {r['restaurant']} | {r['item']}  {price_str}"
            f"  [{r['category']} · {r['menu_type']}]"
        )
        if r["description"]:
            print(f"           {r['description']}")
        print()
