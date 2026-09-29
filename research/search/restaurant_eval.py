"""
Restaurant-level evaluation.

For each benchmark query, computes the *ground-truth* restaurant ranking —
which restaurants SHOULD rank highest — derived purely from relevance_*.csv,
with no search engine involved. This alone is useful for sanity-checking the
judgment data itself (see --show-ground-truth), independent of any engine.

With --engine, additionally builds that engine, ranks restaurants the same
way search_grouped.py would (by each item's rank position in the engine's
flat results — see search_grouped.group_results for why), and scores that
ranking against the ground truth using the same NDCG@N / Recall@N / MRR
evaluate.py uses at the item level — restaurant_scores() is the one place
"group items by restaurant, score by mean of top-K" lives, so both rankings
go through it, just fed different per-item values (relevance grade vs. rank
position).

Usage:
    python restaurant_eval.py --show-ground-truth --query-id C02-07   # one query, no engine
    python restaurant_eval.py --show-ground-truth --category C21     # ground truth per query in a category
    python restaurant_eval.py --engine colbert                        # full comparison, all queries
    python restaurant_eval.py --engine soft_bm25 --vectors models/numberbatch-en.txt --category C11
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids
from lib.ranking import restaurant_scores
from evaluate import load_queries, load_relevance, ndcg_at_k, recall_at_k, reciprocal_rank, aggregate_scores


def ground_truth_ranking(
    qid: str,
    judgments: dict[tuple[str, str], dict[str, int]],
    k_items: int,
) -> list[tuple[str, float, list[float]]]:
    """
    Ideal restaurant ranking for one query, derived purely from relevance_*.csv.
    Only restaurants with at least one judged (relevance >= 1) item for this
    query appear — a restaurant with nothing relevant shouldn't be "ranked"
    at all, just absent, same as it would be from search_grouped.py's display.
    """
    item_values: list[tuple[str, float]] = []
    for (rid, q2), items in judgments.items():
        if q2 != qid:
            continue
        for rel in items.values():
            item_values.append((rid, float(rel)))
    return restaurant_scores(item_values, k_items)


def engine_ranking(query_text: str, search_fn, k_items: int) -> list[tuple[str, float, list[float]]]:
    """
    An engine's own restaurant ranking for one query — same rank-position
    logic as search_grouped.group_results, kept in sync deliberately: this
    function should always rank restaurants exactly the way search_grouped.py
    would display them, since the point is to evaluate real display behavior.
    """
    results = search_fn(query_text)
    item_values = [(r["restaurant_id"], 1.0 / (i + 1)) for i, r in enumerate(results)]
    return restaurant_scores(item_values, k_items)


def evaluate_restaurants(
    search_fn,
    *,
    top_restaurants: int = 10,
    top_items: int = 3,
    category: str | None = None,
    difficulty: str | None = None,
    verbose: bool = False,
    restaurant_names: dict[str, str] | None = None,
) -> dict:
    """
    Run every benchmark query's engine restaurant-ranking against the
    ground-truth restaurant ranking. Returns the same overall/by_category/
    by_difficulty/per_query shape as evaluate.evaluate(), at restaurant
    instead of item granularity.
    """
    queries = load_queries(category=category, difficulty=difficulty)
    judgments = load_relevance()
    names = restaurant_names or {}

    ndcg_key = f"ndcg@{top_restaurants}"
    recall_key = f"recall@{top_restaurants}"

    per_query: list[dict] = []
    for q in queries:
        qid = q["query_id"]
        gt = ground_truth_ranking(qid, judgments, top_items)
        gt_score = {rid: score for rid, score, _ in gt}

        eng = engine_ranking(q["query_text"], search_fn, top_items)
        ranked_scores = [gt_score.get(rid, 0.0) for rid, _, _ in eng]

        score = {
            "query_id": qid,
            "query_text": q["query_text"],
            "category_id": q["category_id"],
            "category_name": q["category_name"],
            "difficulty": q["difficulty"],
            "n_gt_restaurants": len(gt),
            ndcg_key: ndcg_at_k(ranked_scores, top_restaurants),
            recall_key: recall_at_k(ranked_scores, top_restaurants),
            "mrr": reciprocal_rank(ranked_scores),
        }
        per_query.append(score)

        if verbose:
            gt_names = [names.get(rid, rid) for rid, _, _ in gt[:3]]
            eng_names = [names.get(rid, rid) for rid, _, _ in eng[:3]]
            print(
                f"  Q{qid:>8} [{q['category_id']}/{q['difficulty'][:1]}]"
                f" NDCG@{top_restaurants}={score[ndcg_key]:.3f}"
                f" Recall@{top_restaurants}={score[recall_key]:.3f}"
                f" MRR={score['mrr']:.3f}"
                f"  «{q['query_text']}»"
            )
            print(f"           ground truth: {gt_names}   engine: {eng_names}")

    return aggregate_scores(per_query, [ndcg_key, recall_key, "mrr"], gate_key="n_gt_restaurants")


def print_ground_truth(
    top_items: int,
    top_restaurants: int,
    restaurant_names: dict[str, str],
    category: str | None = None,
    difficulty: str | None = None,
    query_id: str | None = None,
) -> None:
    """Print the ideal restaurant ranking per query — no engine involved."""
    queries = load_queries(category=category, difficulty=difficulty)
    if query_id:
        queries = [q for q in queries if q["query_id"] == query_id]
    judgments = load_relevance()

    for q in queries:
        qid = q["query_id"]
        gt = ground_truth_ranking(qid, judgments, top_items)
        print(f"\n{qid}  «{q['query_text']}»  [{q['category_id']} {q['category_name']} / {q['difficulty']}]")
        if not gt:
            print("  (no restaurant has any judged item for this query)")
            continue
        for rid, score, values in gt[:top_restaurants]:
            name = restaurant_names.get(rid, rid)
            print(f"  {score:.3f}  {name:<30} top-{top_items} judged values: {values}")


def print_report(results: dict, top_restaurants: int) -> None:
    ndcg_key = f"ndcg@{top_restaurants}"
    recall_key = f"recall@{top_restaurants}"
    o = results["overall"]

    print(f"\n{'='*60}")
    print(f"  Overall  ({o['n_with_judgments']}/{o['n_queries']} queries have a judged restaurant)")
    print(f"{'='*60}")
    print(f"  NDCG@{top_restaurants:<3}   {o[ndcg_key]:.4f}")
    print(f"  Recall@{top_restaurants:<2}  {o[recall_key]:.4f}")
    print(f"  MRR        {o['mrr']:.4f}")

    print(f"\n{'─'*60}")
    print(f"  By category")
    print(f"{'─'*60}")
    for cat, m in sorted(results["by_category"].items()):
        print(
            f"  {cat}  NDCG@{top_restaurants}={m[ndcg_key]:.3f}"
            f"  Recall@{top_restaurants}={m[recall_key]:.3f}"
            f"  MRR={m['mrr']:.3f}"
            f"  n={m['n_queries']}"
            f"  {m['name']}"
        )

    print(f"\n{'─'*60}")
    print(f"  By difficulty")
    print(f"{'─'*60}")
    for diff, m in results["by_difficulty"].items():
        print(
            f"  {diff:<8}  NDCG@{top_restaurants}={m[ndcg_key]:.3f}"
            f"  Recall@{top_restaurants}={m[recall_key]:.3f}"
            f"  MRR={m['mrr']:.3f}"
            f"  n={m['n_queries']}"
        )
    print()


if __name__ == "__main__":
    import argparse
    import engines
    import colbert_search
    import soft_bm25_search

    parser = argparse.ArgumentParser(
        description="Evaluate restaurant-level ranking against ground truth derived from relevance_*.csv",
        parents=[engines.cli_args(), colbert_search.cli_args(), soft_bm25_search.cli_args()],
    )
    parser.add_argument("--category", help="Filter to one category, e.g. C01")
    parser.add_argument("--difficulty", choices=["Easy", "Medium", "Hard"])
    parser.add_argument("--query-id", help="Filter to one query, e.g. C02-07 (only meaningful with --show-ground-truth)")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--show-ground-truth", action="store_true",
        help="Print the ideal restaurant ranking per query and exit — no engine needed "
             "(engine flags are ignored in this mode; --engine defaults to 'text' either way)",
    )
    parser.add_argument("--top-restaurants", type=int, default=3,
                        help="N: how many restaurants define the ranking cutoff for NDCG/Recall "
                             "(default 3 — with only a handful of judged restaurants today, "
                             "N=10 makes Recall@N trivially 1.0; raise this as judged_restaurant_ids() grows)")
    parser.add_argument("--top-items", type=int, default=3,
                        help="K: how many of each restaurant's items to average for its score, "
                             "matching search_grouped.py's --top-items (default 3)")
    args = parser.parse_args()

    restaurants, menus = load_data(judged_restaurant_ids())
    restaurant_names = {rid: r.get("name", rid) for rid, r in restaurants.items()}

    if args.show_ground_truth:
        print_ground_truth(
            args.top_items, args.top_restaurants, restaurant_names,
            category=args.category, difficulty=args.difficulty, query_id=args.query_id,
        )
        sys.exit(0)

    search_fn = engines.build_search_fn(args, restaurants, menus)

    print(f"Running {args.engine} engine against restaurant-level benchmark "
          f"(top_restaurants={args.top_restaurants}, top_items={args.top_items})...")
    if args.verbose:
        print()

    results = evaluate_restaurants(
        search_fn,
        top_restaurants=args.top_restaurants,
        top_items=args.top_items,
        category=args.category,
        difficulty=args.difficulty,
        verbose=args.verbose,
        restaurant_names=restaurant_names,
    )
    print_report(results, args.top_restaurants)
