"""
Approach 4b: ColBERT late-interaction search.

ColBERT (Contextualized Late Interaction over BERT) keeps one vector *per token*
for every indexed item (instead of collapsing to a single sentence vector like
a bi-encoder).  At query time it does MaxSim: for each query token, find the
most similar item token, then sum those per-token maxima.

This is architecturally the same as Soft-BM25's MaxSim loop, but uses vectors
that were explicitly trained for retrieval (not static ConceptNet word vectors).

Model: colbert-ir/colbertv2.0   128-dim L2-normalised token vectors
Library: pylate   (pip install pylate)

Usage:
    python colbert_search.py shellfish pasta
    python colbert_search.py --show-tokens "rich creamy pasta"
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data


_DEFAULT_MODEL = "colbert-ir/colbertv2.0"


# ── text field selection (matches sbert_search.py — no cuisine to avoid false positives) ──

def _item_text(item: dict) -> str:
    parts = [item.get("name", "")]
    if item.get("description"):
        parts.append(item["description"])
    if item.get("category"):
        parts.append(item["category"])
    return ". ".join(p for p in parts if p)


# ── index ─────────────────────────────────────────────────────────────────────

def build_index(
    menus: dict,
    restaurants: dict,
    model,
    batch_size: int = 64,
) -> dict[str, list[dict]]:
    """
    Encode every menu item with ColBERT and store per-token vector matrices.

    Returns:
        index — {restaurant_id: [{"item": item_dict, "vecs": np.ndarray (n_tokens, 128)}, …]}
    """
    # Flatten all items while remembering their restaurant
    all_texts: list[str] = []
    all_meta:  list[tuple[str, dict]] = []   # (restaurant_id, item_dict)

    for rid, items in menus.items():
        for item in items:
            all_texts.append(_item_text(item))
            all_meta.append((rid, item))

    # Encode in batches — returns list[np.ndarray], one matrix per item
    all_vecs = model.encode(all_texts, is_query=False, batch_size=batch_size,
                             show_progress_bar=False)

    index: dict[str, list[dict]] = {}
    for (rid, item), vecs in zip(all_meta, all_vecs):
        entry = {"item": item, "vecs": np.array(vecs, dtype=np.float32)}
        index.setdefault(rid, []).append(entry)

    return index


# ── scoring ───────────────────────────────────────────────────────────────────

def _maxsim(query_vecs: np.ndarray, item_vecs: np.ndarray) -> float:
    """
    Sum of per-query-token maximum cosine similarity over item tokens.
    Both matrices are already L2-normalised by the ColBERT model.
    """
    sims = query_vecs @ item_vecs.T     # (n_q, n_d)
    return float(sims.max(axis=1).sum())


# ── search ────────────────────────────────────────────────────────────────────

def search(
    query: str,
    restaurants: dict,
    index: dict[str, list[dict]],
    model,
) -> list[dict]:
    """
    Return menu items ranked by ColBERT MaxSim score, highest first.
    """
    q_vecs_raw = model.encode([query], is_query=True, show_progress_bar=False)
    q_vecs = np.array(q_vecs_raw[0], dtype=np.float32)   # (n_q_tokens, 128)

    scored: list[tuple[float, dict]] = []
    for rid, entries in index.items():
        restaurant_name = restaurants[rid].get("name", rid)
        for entry in entries:
            score = _maxsim(q_vecs, entry["vecs"])
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
                "n_tokens":    entry["vecs"].shape[0],
            }))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [r for _, r in scored]


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ColBERT late-interaction menu search")
    parser.add_argument("terms", nargs="+", help="Query words")
    parser.add_argument("--model", default=_DEFAULT_MODEL,
                        help=f"ColBERT model (default: {_DEFAULT_MODEL})")
    parser.add_argument("--show-tokens", action="store_true",
                        help="Show number of ColBERT tokens per result")
    args = parser.parse_args()

    query = " ".join(args.terms)

    print("Loading menus…", end=" ", flush=True)
    restaurants, menus = load_data()
    print(f"{sum(len(v) for v in menus.values())} items")

    print(f"Loading ColBERT model '{args.model}'…", end=" ", flush=True)
    from pylate import models as pylate_models
    model = pylate_models.ColBERT(args.model)
    print("done")

    print("Building index…", end=" ", flush=True)
    index = build_index(menus, restaurants, model)
    n_items = sum(len(v) for v in index.values())
    print(f"{n_items} items encoded")

    print(f"\nQuery: '{query}'\n")
    results = search(query, restaurants, index, model)

    if not results:
        print("No results.")
    for r in results[:20]:
        price_str = (
            f"${r['price']:.2f}" if r["price"] is not None
            else r["price_raw"] or "N/A"
        )
        tok_str = f"  ({r['n_tokens']} tokens)" if args.show_tokens else ""
        print(f"  [{r['score']:.4f}] {r['restaurant']} | {r['item']}  {price_str}"
              f"  [{r['category']} · {r['menu_type']}]{tok_str}")
        if r["description"]:
            print(f"           {r['description']}")
        print()
