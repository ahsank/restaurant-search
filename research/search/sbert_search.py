"""
Approach 4: Sentence-Transformer (SBERT) bi-encoder search.

Each menu item is encoded once into a dense vector at index time.
At query time the query is encoded and items are ranked by cosine similarity.
The model reads the full item string in one forward pass, so phrase context
("not spicy", "oyster sauce") is captured without explicit phrase detection.

Item text includes name, description, category, menu type, and dietary annotations
(matching colbert_search.py and crossencoder_search.py).

Default model: all-MiniLM-L6-v2 (~80 MB, 384 dimensions)
  fast, strong general-purpose retrieval baseline

Other good options:
  multi-qa-MiniLM-L6-cos-v1   — fine-tuned for question-answer retrieval
  all-mpnet-base-v2            — higher quality, slower (~420 MB)
  BAAI/bge-small-en-v1.5      — strong retrieval, 33M params

Usage:
  python sbert_search.py seafood italian
  python sbert_search.py --model multi-qa-MiniLM-L6-cos-v1 spicy noodles
  python sbert_search.py oyster

The model is downloaded automatically on first use and cached in
~/.cache/torch/sentence_transformers/.
"""

import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args


def _item_text(item: dict) -> str:
    """
    Build text for SBERT bi-encoder encoding:
    item name, description, category, menu type, and dietary annotations (matches colbert_search.py and crossencoder_search.py).
    """
    parts = [item.get("name", "")]
    if item.get("description"):
        parts.append(item["description"])
    if item.get("category"):
        parts.append(item["category"])
    if item.get("menu_type"):
        parts.append(item["menu_type"])
    if item.get("dietary"):
        parts.append(item["dietary"])
    return ". ".join(p for p in parts if p)


item_text = _item_text


def build_index(
    menus: dict,
    restaurants: dict,
    model: SentenceTransformer,
    batch_size: int = 64,
) -> dict[str, list[dict]]:
    """
    Encode every menu item once and store unit-normalised vectors.

    Returns:
      index — {restaurant_id: [{"item": item_dict, "vec": np.ndarray}, …]}
    """
    index: dict[str, list[dict]] = {}
    for rid, items in menus.items():
        texts = [_item_text(item) for item in items]
        vecs = model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        index[rid] = [
            {"item": item, "vec": vec}
            for item, vec in zip(items, vecs)
        ]
    return index


def search(
    query: str,
    restaurants: dict,
    index: dict[str, list[dict]],
    model: SentenceTransformer,
) -> list[dict]:
    """
    Encode query and rank all indexed items by cosine similarity.

    Since vectors are unit-normalised, cosine similarity == dot product.
    """
    query_vec = model.encode(query, normalize_embeddings=True)

    scored: list[tuple[float, dict]] = []
    for rid, entries in index.items():
        restaurant_name = restaurants[rid].get("name", rid)
        for entry in entries:
            score = float(np.dot(query_vec, entry["vec"]))
            item = entry["item"]
            scored.append((score, {
                "restaurant":  restaurant_name,
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
        description="SBERT bi-encoder menu search (Approach 4)",
        parents=[restaurant_scope_cli_args()],
    )
    parser.add_argument(
        "--model", default="all-MiniLM-L6-v2",
        help="Sentence-transformers model name (default: all-MiniLM-L6-v2)",
    )
    parser.add_argument("terms", nargs="+", help="Query words")
    args = parser.parse_args()

    print(f"Loading model '{args.model}'...", end=" ", flush=True)
    model = SentenceTransformer(args.model)
    print("done")

    print("Loading menus and building index...", end=" ", flush=True)
    restaurants, menus = load_data(judged_restaurant_ids() if args.benchmark_only else None)
    index = build_index(menus, restaurants, model)
    total = sum(len(v) for v in index.values())
    print(f"{total} items encoded")

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
