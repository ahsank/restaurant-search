"""
Evaluate a search function against the benchmark in data/queries/.

Usage:
    python3 research/search/evaluate.py                    # runs text_search baseline
    python3 research/search/evaluate.py --category C01     # filter by category
    python3 research/search/evaluate.py --difficulty Easy  # filter by difficulty

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
from lib.data import load_data


# ---------------------------------------------------------------------------
# Benchmark loading
# ---------------------------------------------------------------------------

def load_queries(category: str | None = None, difficulty: str | None = None) -> list[dict]:
    rows = []
    with open(_QUERIES_DIR / "queries.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if category and row["category_id"] != category:
                continue
            if difficulty and row["difficulty"] != difficulty:
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
# Evaluation loop
# ---------------------------------------------------------------------------

def evaluate(
    search_fn,
    *,
    k_ndcg: int = 5,
    k_recall: int = 10,
    category: str | None = None,
    difficulty: str | None = None,
    verbose: bool = False,
) -> dict:
    """
    Run all benchmark queries through search_fn and return aggregated metrics.

    search_fn(query: str) -> list[dict]   where each dict has "restaurant_id" and "name"
    """
    queries = load_queries(category=category, difficulty=difficulty)
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

    def avg(key: str, rows=per_query) -> float:
        vals = [r[key] for r in rows if r["n_relevant"] > 0]
        return sum(vals) / len(vals) if vals else 0.0

    ndcg_key = f"ndcg@{k_ndcg}"
    recall_key = f"recall@{k_recall}"

    # Overall
    overall = {
        ndcg_key: avg(ndcg_key),
        recall_key: avg(recall_key),
        "mrr": avg("mrr"),
        "n_queries": len(per_query),
        "n_with_judgments": sum(1 for r in per_query if r["n_relevant"] > 0),
    }

    # By category
    by_category: dict[str, dict] = {}
    cat_ids = sorted({r["category_id"] for r in per_query})
    for cat in cat_ids:
        rows = [r for r in per_query if r["category_id"] == cat]
        by_category[cat] = {
            "name": rows[0]["category_name"],
            ndcg_key: avg(ndcg_key, rows),
            recall_key: avg(recall_key, rows),
            "mrr": avg("mrr", rows),
            "n_queries": len(rows),
        }

    # By difficulty
    by_difficulty: dict[str, dict] = {}
    for diff in ("Easy", "Medium", "Hard"):
        rows = [r for r in per_query if r["difficulty"] == diff]
        if rows:
            by_difficulty[diff] = {
                ndcg_key: avg(ndcg_key, rows),
                recall_key: avg(recall_key, rows),
                "mrr": avg("mrr", rows),
                "n_queries": len(rows),
            }

    return {
        "overall": overall,
        "by_category": by_category,
        "by_difficulty": by_difficulty,
        "per_query": per_query,
    }


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

    # Needed before parser construction, not just before the engine branches below,
    # since colbert_search/soft_bm25_search's own flags are pulled in via parents=.
    sys.path.insert(0, str(_ROOT / "research" / "search"))
    import colbert_search
    import soft_bm25_search

    parser = argparse.ArgumentParser(
        description="Evaluate search against the benchmark",
        parents=[colbert_search.cli_args(), soft_bm25_search.cli_args()],
    )
    parser.add_argument("--category", help="Filter to one category, e.g. C01")
    parser.add_argument("--difficulty", choices=["Easy", "Medium", "Hard"])
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--engine",
        choices=["text", "enhanced", "filtered", "soft_bm25", "sbert", "colbert"],
        default="text",
        help="Search engine: text (baseline), enhanced, filtered, soft_bm25, sbert, colbert (default: text)",
    )
    parser.add_argument(
        "--model", default="all-MiniLM-L6-v2",
        help="Sentence-transformers model name (default: all-MiniLM-L6-v2, used by --engine sbert)",
    )
    args = parser.parse_args()

    # Load data once — all engines share the same restaurants/menus.
    restaurants, menus = load_data()
    name_to_id = {v.get("name", k): k for k, v in restaurants.items()}

    if args.engine in ("enhanced", "filtered"):
        from enhanced_text_search import search as _enhanced_search
        _filter = args.engine == "filtered"
        def _raw_search(query, restaurants, menus):
            return _enhanced_search(query, restaurants, menus, filter_restaurant_ctx=_filter)

    elif args.engine == "soft_bm25":
        if args.segmenter == "fmm":
            if not args.vectors:
                parser.error("--vectors PATH is required for --engine soft_bm25 --segmenter fmm")
            from soft_bm25_search import (
                load_conceptnet, PhraseTokenizer, VectorStore, build_index,
                search as _sbm25_search,
            )
            print("Loading vectors...", end=" ", flush=True)
            _raw_vecs, _phrase_vocab = load_conceptnet(args.vectors)
            print(f"{len(_raw_vecs):,} entries")
            _tokenizer = PhraseTokenizer(_phrase_vocab, max_phrase_len=args.max_phrase_len)
            _vstore    = VectorStore(_raw_vecs, composition=args.composition)
            print("Building index...", end=" ", flush=True)
            _index, _idf, _avgdl = build_index(menus, _tokenizer, _vstore)
            print(f"{sum(len(v) for v in _index.values())} items indexed")

            _corrector = None
            if args.spell_correct:
                from soft_bm25_search import SpellCorrector
                _corrector = SpellCorrector()

            def _raw_search(query, _restaurants, _menus):
                return _sbm25_search(query, restaurants, _index, _idf, _tokenizer, _vstore, _avgdl,
                                     similarity_threshold=args.threshold, k1=args.k1, b=args.b,
                                     combiner=args.combiner, spell_corrector=_corrector)
        else:
            from soft_bm25_search import (
                SpacyBertEncoder, BertSubwordEncoder,
                build_index_contextual, search_contextual as _sbm25_ctx_search,
            )
            print(f"Loading BERT encoder ({args.segmenter})...", flush=True)
            _encoder = (
                SpacyBertEncoder() if args.segmenter == "spacy_bert"
                else BertSubwordEncoder()
            )
            print("Building index...")
            _index, _idf, _avgdl = build_index_contextual(menus, _encoder)
            print(f"  {sum(len(v) for v in _index.values())} items indexed, avgdl={_avgdl:.1f}")

            def _raw_search(query, _restaurants, _menus):
                return _sbm25_ctx_search(query, restaurants, _index, _idf, _encoder, _avgdl,
                                         similarity_threshold=args.threshold, k1=args.k1, b=args.b,
                                         combiner=args.combiner)

    elif args.engine == "sbert":
        from sbert_search import build_index as _sbert_build_index, search as _sbert_search
        from sentence_transformers import SentenceTransformer
        print(f"Loading model '{args.model}'...", end=" ", flush=True)
        _sbert_model = SentenceTransformer(args.model)
        print("done")
        print("Building index...", end=" ", flush=True)
        _sbert_index = _sbert_build_index(menus, restaurants, _sbert_model)
        print(f"{sum(len(v) for v in _sbert_index.values())} items encoded")

        def _raw_search(query, _restaurants, _menus):
            return _sbert_search(query, restaurants, _sbert_index, _sbert_model)

    elif args.engine == "colbert":
        from colbert_search import build_index as _cb_build_index, search as _cb_search
        from pylate import models as pylate_models
        _cb_model_name = args.model if args.model != "all-MiniLM-L6-v2" else "colbert-ir/colbertv2.0"
        print(f"Loading ColBERT model '{_cb_model_name}' (query_length={args.query_length or 'model default'})...", end=" ", flush=True)
        _cb_model = pylate_models.ColBERT(_cb_model_name, query_length=args.query_length)
        print("done")
        print("Building index...", end=" ", flush=True)
        _cb_index = _cb_build_index(menus, restaurants, _cb_model)
        print(f"{sum(len(v) for v in _cb_index.values())} items encoded")

        def _raw_search(query, _restaurants, _menus):
            return _cb_search(query, restaurants, _cb_index, _cb_model)

    else:
        from text_search import search as _raw_search

    def search(query: str) -> list[dict]:
        raw = _raw_search(query, restaurants, menus)
        out = []
        for r in raw:
            rid = name_to_id.get(r["restaurant"], r["restaurant"])
            out.append({"restaurant_id": rid, "name": r["item"], **r})
        return out

    print(f"Running {args.engine} engine against benchmark...")
    if args.verbose:
        print()

    results = evaluate(
        search,
        category=args.category,
        difficulty=args.difficulty,
        verbose=args.verbose,
    )
    print_report(results)
