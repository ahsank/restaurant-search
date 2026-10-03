"""
Evaluate a search function against the benchmark in data/queries/.

Usage:
    python3 research/search/evaluate.py                    # runs text_search baseline
    python3 research/search/evaluate.py --category C01     # filter by category
    python3 research/search/evaluate.py --difficulty Easy  # filter by difficulty

Restaurant scope: always restricted to judged_restaurant_ids() — restaurants
that have a data/queries/relevance_<id>.csv file — never all of data/menus/.
This is not a flag; evaluating against unjudged restaurants would only ever
score a correct hit there as a false positive (no ground truth to credit it
against), so there's no scenario where searching the full corpus here is
correct. As more restaurants are added to data/menus/ without judgments yet,
this keeps the benchmark run scoped to just the curated subset automatically.

Interface for custom search functions:
    The search function must accept (query: str) -> list[dict], where each dict
    has at least "restaurant_id" and "name" keys (same shape returned by load_data()).
    Results must be ordered best-first; the list length determines the cutoff.
"""

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
_QUERIES_DIR = _ROOT / "data" / "queries"

sys.path.insert(0, str(_ROOT / "research"))
from lib.data import load_data, judged_restaurant_ids


# ---------------------------------------------------------------------------
# Benchmark loading
# ---------------------------------------------------------------------------

def load_queries(
    category: str | None = None,
    difficulty: str | None = None,
    query_ids: set[str] | None = None,
) -> list[dict]:
    """
    query_ids: if given, only include queries whose query_id is in this set.
    Used to score a finetuned model (Approach 5) exclusively against queries
    held out of its training triples — see research/data_gen/mine_hard_negatives.py's
    --held-out-file — so the benchmark number isn't inflated by the model
    having partially memorized eval queries during training.
    """
    rows = []
    with open(_QUERIES_DIR / "queries.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if category and row["category_id"] != category:
                continue
            if difficulty and row["difficulty"] != difficulty:
                continue
            if query_ids is not None and row["query_id"] not in query_ids:
                continue
            rows.append(row)
    return rows


def load_relevance() -> dict[tuple[str, str], dict[str, int]]:
    """Return {(restaurant_id, query_id): {item_name: relevance}}."""
    judgments: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    for path in sorted(_QUERIES_DIR.glob("relevance_*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["restaurant"], row["query_id"])
                judgments[key][row["menu_item"]] = int(row["relevance"])
    return dict(judgments)


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def _dcg(rels: list[int], k: int) -> float:
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels[:k]))


def ndcg_at_k(ranked_rels: list[int], k: int) -> float:
    ideal = sorted(ranked_rels, reverse=True)
    idcg = _dcg(ideal, k)
    return _dcg(ranked_rels, k) / idcg if idcg > 0 else 0.0


def recall_at_k(ranked_rels: list[int], k: int) -> float:
    n_rel = sum(1 for r in ranked_rels if r > 0)
    if n_rel == 0:
        return 0.0
    return sum(1 for r in ranked_rels[:k] if r > 0) / n_rel


def reciprocal_rank(ranked_rels: list[int]) -> float:
    for i, r in enumerate(ranked_rels):
        if r > 0:
            return 1.0 / (i + 1)
    return 0.0


# ---------------------------------------------------------------------------
# Aggregation (shared with restaurant_eval.py — same rollup shape, different
# per-query rows: item-level ndcg/recall/mrr here, restaurant-level there)
# ---------------------------------------------------------------------------

def aggregate_scores(per_query: list[dict], score_keys: list[str], gate_key: str) -> dict:
    """
    Aggregate per-query score rows into overall / by_category / by_difficulty.
    Only rows where row[gate_key] > 0 count toward the averages — queries with
    no ground truth for this metric are excluded from the average, not scored
    as 0 (a query nobody judged shouldn't drag the average down).

    Each row must have "category_id", "category_name", "difficulty", gate_key,
    and every key in score_keys (e.g. "ndcg@5", "recall@10", "mrr").
    """
    def avg(key: str, rows=per_query) -> float:
        vals = [r[key] for r in rows if r[gate_key] > 0]
        return sum(vals) / len(vals) if vals else 0.0

    overall = {k: avg(k) for k in score_keys}
    overall["n_queries"] = len(per_query)
    overall["n_with_judgments"] = sum(1 for r in per_query if r[gate_key] > 0)

    by_category: dict[str, dict] = {}
    for cat in sorted({r["category_id"] for r in per_query}):
        rows = [r for r in per_query if r["category_id"] == cat]
        by_category[cat] = {
            "name": rows[0]["category_name"],
            "n_queries": len(rows),
            **{k: avg(k, rows) for k in score_keys},
        }

    by_difficulty: dict[str, dict] = {}
    for diff in ("Easy", "Medium", "Hard"):
        rows = [r for r in per_query if r["difficulty"] == diff]
        if rows:
            by_difficulty[diff] = {
                "n_queries": len(rows),
                **{k: avg(k, rows) for k in score_keys},
            }

    return {
        "overall": overall,
        "by_category": by_category,
        "by_difficulty": by_difficulty,
        "per_query": per_query,
    }


# ---------------------------------------------------------------------------
# Evaluation loop
# ---------------------------------------------------------------------------

def evaluate(
    search_fn,
    *,
    k_ndcg: int = 5,
    k_recall: int = 10,
    category: str | None = None,
    difficulty: str | None = None,
    query_ids: set[str] | None = None,
    verbose: bool = False,
) -> dict:
    """
    Run all benchmark queries through search_fn and return aggregated metrics.

    search_fn(query: str) -> list[dict]   where each dict has "restaurant_id" and "name"
    """
    queries = load_queries(category=category, difficulty=difficulty, query_ids=query_ids)
    judgments = load_relevance()

    per_query: list[dict] = []

    for q in queries:
        qid = q["query_id"]
        results = search_fn(q["query_text"])

        ranked_rels: list[int] = []
        for item in results:
            rid = item["restaurant_id"]
            name = item["name"]
            rel = judgments.get((rid, qid), {}).get(name, 0)
            ranked_rels.append(rel)

        # Collect all known relevance values for this query (across all restaurants)
        all_rels = []
        for (rid, q2), items in judgments.items():
            if q2 == qid:
                all_rels.extend(items.values())
        n_relevant = sum(1 for r in all_rels if r > 0)

        score = {
            "query_id": qid,
            "query_text": q["query_text"],
            "category_id": q["category_id"],
            "category_name": q["category_name"],
            "difficulty": q["difficulty"],
            "n_results": len(results),
            "n_relevant": n_relevant,
            f"ndcg@{k_ndcg}": ndcg_at_k(ranked_rels, k_ndcg),
            f"recall@{k_recall}": recall_at_k(ranked_rels, k_recall),
            "mrr": reciprocal_rank(ranked_rels),
        }
        per_query.append(score)

        if verbose:
            print(
                f"  Q{qid:>3} [{q['category_id']}/{q['difficulty'][:1]}]"
                f" NDCG@{k_ndcg}={score[f'ndcg@{k_ndcg}']:.3f}"
                f" Recall@{k_recall}={score[f'recall@{k_recall}']:.3f}"
                f" MRR={score['mrr']:.3f}"
                f"  «{q['query_text']}»"
            )

    ndcg_key = f"ndcg@{k_ndcg}"
    recall_key = f"recall@{k_recall}"
    return aggregate_scores(per_query, [ndcg_key, recall_key, "mrr"], gate_key="n_relevant")


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def print_report(results: dict, k_ndcg: int = 5, k_recall: int = 10) -> None:
    ndcg_key = f"ndcg@{k_ndcg}"
    recall_key = f"recall@{k_recall}"
    o = results["overall"]

    print(f"\n{'='*60}")
    print(f"  Overall  ({o['n_with_judgments']}/{o['n_queries']} queries have judgments)")
    print(f"{'='*60}")
    print(f"  NDCG@{k_ndcg:<3}   {o[ndcg_key]:.4f}")
    print(f"  Recall@{k_recall:<2}  {o[recall_key]:.4f}")
    print(f"  MRR        {o['mrr']:.4f}")

    print(f"\n{'─'*60}")
    print(f"  By category")
    print(f"{'─'*60}")
    for cat, m in sorted(results["by_category"].items()):
        print(
            f"  {cat}  NDCG@{k_ndcg}={m[ndcg_key]:.3f}"
            f"  Recall@{k_recall}={m[recall_key]:.3f}"
            f"  MRR={m['mrr']:.3f}"
            f"  n={m['n_queries']}"
            f"  {m['name']}"
        )

    print(f"\n{'─'*60}")
    print(f"  By difficulty")
    print(f"{'─'*60}")
    for diff, m in results["by_difficulty"].items():
        print(
            f"  {diff:<8}  NDCG@{k_ndcg}={m[ndcg_key]:.3f}"
            f"  Recall@{k_recall}={m[recall_key]:.3f}"
            f"  MRR={m['mrr']:.3f}"
            f"  n={m['n_queries']}"
        )
    print()


# ---------------------------------------------------------------------------
# CLI entry point (uses text_search baseline)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    # Needed before parser construction, not just before build_search_fn() below,
    # since colbert_search/soft_bm25_search/engines' own flags are pulled in via parents=.
    sys.path.insert(0, str(_ROOT / "research" / "search"))
    import colbert_search
    import soft_bm25_search
    import engines

    parser = argparse.ArgumentParser(
        description="Evaluate search against the benchmark",
        parents=[engines.cli_args(), colbert_search.cli_args(), soft_bm25_search.cli_args()],
    )
    parser.add_argument("--category", help="Filter to one category, e.g. C01")
    parser.add_argument("--difficulty", choices=["Easy", "Medium", "Hard"])
    parser.add_argument("--query-ids-file", type=Path,
                        help="Score only query_ids listed in this file (one per line) — e.g. "
                             "research/data_gen/held_out_query_ids.txt, to evaluate a finetuned "
                             "model (Approach 5) exclusively on queries it never trained on")
    parser.add_argument("--exclude-query-ids-file", type=Path,
                        help="Skip query_ids listed in this file (one per line) — e.g. the gap_query_id "
                             "values in gap_fill_triples.jsonl, to score only the queries a model was "
                             "NOT patched on (the leakage check for Approach 5 variant 3 / Approach 6)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    query_ids = None
    if args.query_ids_file:
        query_ids = {line.strip() for line in args.query_ids_file.read_text().splitlines() if line.strip()}
    if args.exclude_query_ids_file:
        excluded = {line.strip() for line in args.exclude_query_ids_file.read_text().splitlines() if line.strip()}
        if query_ids is None:
            query_ids = {q["query_id"] for q in load_queries()}
        query_ids -= excluded

    # Load data once — all engines share the same restaurants/menus. Always scoped
    # to judged restaurants; see the module docstring for why this isn't a flag.
    restaurants, menus = load_data(judged_restaurant_ids())
    search = engines.build_search_fn(args, restaurants, menus)

    print(f"Running {args.engine} engine against benchmark...")
    if args.verbose:
        print()

    results = evaluate(
        search,
        category=args.category,
        difficulty=args.difficulty,
        query_ids=query_ids,
        verbose=args.verbose,
    )
    print_report(results)
