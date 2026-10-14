"""
Approach 7b: Hybrid search (LLM candidate retrieval + CrossEncoder reranking).

Combines the high candidate recall of the LLM reader (Approach 7) with the
fine-grained scoring and ordering of a cross-encoder (Approach 6).

Architecture:
1. Candidate retrieval: Replays LLM candidate rankings (--rankings JSONL).
   The LLM reader acts as a high-recall filter (~25 items/query on average).
2. Cross-encoder rescoring: Each candidate item is rescored using a
   CrossEncoder (--model, default: cross-encoder/ms-marco-MiniLM-L6-v2) on
   (query, candidate_text). Candidate text includes item name, description,
   category, menu type, and dietary metadata.
3. LLM grade boost & strict grade:
   - By default, score = cross_encoder_score + grade_boost * grade
     (default grade_boost = 0.0, using pure cross-encoder scoring).
   - If --strict-grade is set, items are ranked strictly by LLM grade first
     (grade 2 before grade 1), breaking intra-grade ties by CrossEncoder score.
4. Fallback: If the LLM returned no matches for a query (or the query is missing
   from the rankings), falls back to full cross-encoder search over all menu items.

Usage:
    python research/search/hybrid_search.py --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl seafood italian
    python research/search/hybrid_search.py --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --grade-boost 1.0 spicy noodles
    python research/search/hybrid_search.py --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --strict-grade vegan noodles

Via evaluate.py:
    python research/search/evaluate.py --engine hybrid \\
        --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl \\
        --model cross-encoder/ms-marco-MiniLM-L6-v2 --strict-grade
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

from sentence_transformers.cross_encoder import CrossEncoder

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args
import search.crossencoder_search as ce_search

STOCK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


def candidate_item_text(item: dict) -> str:
    """
    Build candidate text for CrossEncoder rescoring:
    item name, description, category, menu type, and dietary annotations.
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


_item_text = candidate_item_text


def cli_args() -> argparse.ArgumentParser:
    """Reusable CLI flags for hybrid search (see engines.py)."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--rankings", type=Path,
        help="Rankings JSONL written by llm_search.py; required for hybrid search",
    )
    parser.add_argument(
        "--grade-boost", type=float, default=0.0,
        help="Boost added to cross-encoder score per LLM grade (default: 0.0)",
    )
    parser.add_argument(
        "--strict-grade", action="store_true",
        help="Rank items strictly by LLM grade first (2 before 1), breaking intra-grade ties by CrossEncoder score",
    )
    return parser


def load_rankings(path: Path | str) -> dict[str, list[dict]]:
    """Load {query_text: ranked results} from a rankings JSONL (meta line skipped)."""
    rankings = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "query_text" in row:
                rankings[row["query_text"]] = row.get("results", [])
    return rankings


def build_item_map(menus: dict) -> dict[tuple[str, str], tuple[dict, str]]:
    """
    Map (restaurant_id, item_name) -> (item_dict, candidate_text).
    If an item name appears multiple times under a restaurant (e.g. lunch and dinner),
    keeps the first entry.
    """
    item_map = {}
    for rid, items in menus.items():
        for item in items:
            key = (rid, item["name"])
            if key not in item_map:
                item_map[key] = (item, candidate_item_text(item))
    return item_map


def _find_item_fallback(rid: str, name: str, menus: dict) -> tuple[dict, str]:
    """Fallback search in menus[rid] if an exact (rid, name) lookup misses."""
    items = menus.get(rid, [])
    name_lower = name.lower().strip()
    for item in items:
        if item["name"].lower().strip() == name_lower:
            return item, candidate_item_text(item)
    # Synthetic item dict if completely unindexed
    synthetic = {
        "name": name,
        "description": "",
        "dietary": "",
        "price": None,
        "price_raw": "",
        "category": "",
        "menu_type": "",
        "restaurant_id": rid,
    }
    return synthetic, name


def search(
    query: str,
    rankings: dict[str, list[dict]],
    restaurants: dict,
    menus: dict,
    model: CrossEncoder,
    item_map: dict[tuple[str, str], tuple[dict, str]],
    ce_index: list[tuple[str, dict, str]],
    grade_boost: float = 0.0,
    strict_grade: bool = False,
    batch_size: int = 128,
) -> list[dict]:
    """
    Perform hybrid search for a single query:
    Rescores LLM candidates using CrossEncoder; falls back to full cross-encoder
    search if the candidate list is empty.
    """
    name_to_id = {v.get("name", k): k for k, v in restaurants.items()}
    candidates = rankings.get(query)
    if candidates is None:
        candidates = rankings.get(query.strip(), [])

    # Fallback to full cross-encoder search when no LLM candidates match
    if not candidates:
        raw_results = ce_search.search(query, restaurants, ce_index, model, batch_size=batch_size)
        out = []
        for r in raw_results:
            rid = name_to_id.get(r["restaurant"], r.get("restaurant_id", r["restaurant"]))
            out.append({
                "restaurant_id": rid,
                "name": r["item"],
                **r,
            })
        return out

    # Rescore LLM candidates with CrossEncoder
    pairs = []
    c_list = []
    for c in candidates:
        rid = c.get("restaurant_id")
        name = c.get("name")
        grade_val = c.get("grade")
        grade = int(grade_val) if grade_val is not None else 1
        if (rid, name) in item_map:
            item, text = item_map[(rid, name)]
        else:
            item, text = _find_item_fallback(rid, name, menus)
        pairs.append((query, text))
        c_list.append((rid, item, grade))

    scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)

    scored: list[tuple[float, float, dict]] = []
    for (rid, item, grade), score in zip(c_list, scores):
        raw_ce_score = float(score)
        final_score = raw_ce_score + grade_boost * grade
        r_display = restaurants.get(rid, {}).get("name", rid) if isinstance(restaurants.get(rid), dict) else rid
        scored.append((final_score, raw_ce_score, {
            "restaurant_id": rid,
            "restaurant": r_display,
            "name": item["name"],
            "item": item["name"],
            "description": item.get("description", ""),
            "dietary": item.get("dietary", ""),
            "price": item.get("price"),
            "price_raw": item.get("price_raw", ""),
            "category": item.get("category", ""),
            "menu_type": item.get("menu_type", ""),
            "score": round(final_score, 4),
            "grade": grade,
        }))

    if strict_grade:
        scored.sort(key=lambda t: (t[2]["grade"], t[1]), reverse=True)
    else:
        scored.sort(key=lambda t: t[0], reverse=True)
    return [r for _, _, r in scored]


def build_search_fn(
    rankings_path: Path | str,
    model_name: str,
    restaurants: dict,
    menus: dict,
    grade_boost: float = 0.0,
    strict_grade: bool = False,
    batch_size: int = 128,
) -> Callable[[str], list[dict]]:
    """Build a search_fn(query) -> list[dict] suitable for evaluate.py / engines.py."""
    print(f"Loading LLM rankings from '{rankings_path}'...", end=" ", flush=True)
    rankings = load_rankings(rankings_path)
    print(f"{len(rankings)} queries loaded")

    print(f"Loading CrossEncoder model '{model_name}'...", end=" ", flush=True)
    model = CrossEncoder(model_name)
    print("done")

    item_map = build_item_map(menus)
    ce_index = [
        (rid, item, candidate_item_text(item))
        for rid, items in menus.items()
        for item in items
    ]

    def search_fn(query: str) -> list[dict]:
        return search(
            query=query,
            rankings=rankings,
            restaurants=restaurants,
            menus=menus,
            model=model,
            item_map=item_map,
            ce_index=ce_index,
            grade_boost=grade_boost,
            strict_grade=strict_grade,
            batch_size=batch_size,
        )

    return search_fn


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Hybrid menu search (LLM candidate retrieval + CrossEncoder reranking)",
        parents=[cli_args(), restaurant_scope_cli_args()],
    )
    parser.add_argument("terms", nargs="+", help="Query words")
    parser.add_argument(
        "--model", default=STOCK_MODEL,
        help=f"Cross-encoder model (default: {STOCK_MODEL})",
    )
    args = parser.parse_args()

    if not args.rankings:
        sys.exit("Error: --rankings FILE is required (path to rankings JSONL from llm_search.py)")

    restaurants, menus = load_data(judged_restaurant_ids() if args.benchmark_only else None)
    search_fn = build_search_fn(
        rankings_path=args.rankings,
        model_name=args.model,
        restaurants=restaurants,
        menus=menus,
        grade_boost=args.grade_boost,
        strict_grade=args.strict_grade,
    )

    query = " ".join(args.terms)
    print(f"\nQuery: '{query}'\n")

    results = search_fn(query)

    if not results:
        print("  (no matches)")
    for r in results[:20]:
        price_str = (
            f"${r['price']:.2f}" if r["price"] is not None
            else r["price_raw"] or "N/A"
        )
        grade_str = f" [grade {r['grade']}]" if "grade" in r else ""
        dietary_str = f" ({r['dietary']})" if r.get("dietary") else ""
        print(
            f"  [{r['score']:.4f}]{grade_str} {r['restaurant']} | {r['item']}  {price_str}"
            f"  [{r['category']} · {r['menu_type']}]{dietary_str}"
        )
        if r["description"]:
            print(f"           {r['description']}")
        print()
