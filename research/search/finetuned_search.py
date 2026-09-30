"""
Approach 5: search using the bi-encoder finetuned by
research/train/finetune_biencoder.py on hard-negative triples from
research/data_gen/mine_hard_negatives.py.

This is otherwise identical to sbert_search.py (Approach 4) — a finetuned
model is still just a SentenceTransformer, loaded from a local directory
instead of a hub name — so indexing/scoring is reused directly rather than
duplicated. This script only changes the default model path and CLI framing.

Usage:
    python search/finetuned_search.py seafood italian
    python search/finetuned_search.py --model models/finetuned-all-mpnet-base-v2 spicy noodles

Equivalent via the shared --engine dispatcher (used by evaluate.py):
    python search/evaluate.py --engine sbert --model models/finetuned-all-MiniLM-L6-v2
"""

import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args

from sbert_search import build_index, search

_ROOT = Path(__file__).parents[2]
_DEFAULT_MODEL = _ROOT / "models" / "finetuned-all-MiniLM-L6-v2"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Finetuned bi-encoder menu search (Approach 5)",
        parents=[restaurant_scope_cli_args()],
    )
    parser.add_argument(
        "--model", default=str(_DEFAULT_MODEL),
        help=f"Path to a finetuned model directory (default: {_DEFAULT_MODEL})",
    )
    parser.add_argument("terms", nargs="+", help="Query words")
    args = parser.parse_args()

    if not Path(args.model).exists():
        raise SystemExit(
            f"Model not found at '{args.model}'. Train one first:\n"
            f"  python research/data_gen/mine_hard_negatives.py\n"
            f"  python research/train/finetune_biencoder.py"
        )

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
