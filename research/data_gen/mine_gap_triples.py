"""
Approach 5 data generation, variant 3: a small, targeted patch for whatever
queries a given finetuned model currently does worst on — not a broad mining
pass like mine_hard_negatives.py or generate_synthetic_data.py.

Diagnosis: run the model against the full benchmark, take the N queries with
the lowest NDCG@5 (that have at least one real judgment), and for each one
pair the ground-truth best item (the real fix) against the model's own
current top wrong answer (the real mistake) — real retriever-error mining,
but scoped to only the queries currently failing, not a general sweep.

Leakage note: the anchor is NOT the literal benchmark query_text — `claude -p`
is asked to reword it (same intent, different phrasing) specifically so
training doesn't just memorize the exact eval string. Some signal still
transfers to that exact query (that's the point — it's a targeted patch), so
after retraining, check both (a) the targeted queries themselves and (b)
OTHER, non-targeted queries in the same weak categories — improvement on (b)
is the real evidence this generalizes rather than memorizes.

Usage:
    python research/data_gen/mine_gap_triples.py
    python research/data_gen/mine_gap_triples.py --model models/finetuned-synthetic-all-MiniLM-L6-v2 --count 30
    python research/data_gen/mine_gap_triples.py --ndcg-threshold 0.3 --count 40

Output: research/data_gen/gap_fill_triples.jsonl — small, JSONL of
    {"anchor", "positive", "negative", "source", "gap_query_id"} rows.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "research"))
from lib.data import load_data, judged_restaurant_ids

sys.path.insert(0, str(_ROOT / "research" / "search"))
from sbert_search import _item_text, build_index, search as _sbert_search
from evaluate import evaluate, load_relevance

_DEFAULT_OUT = Path(__file__).parent / "gap_fill_triples.jsonl"
_DEFAULT_MODEL = _ROOT / "models" / "finetuned-synthetic-all-MiniLM-L6-v2"
_DEFAULT_LLM_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_COUNT = 30
_DEFAULT_NDCG_THRESHOLD = 0.3


def find_gap_queries(search_fn, count: int, ndcg_threshold: float) -> list[dict]:
    """Worst-NDCG@5 queries (with real judgments), ascending."""
    results = evaluate(search_fn)
    candidates = [r for r in results["per_query"] if r["n_relevant"] > 0 and r["ndcg@5"] < ndcg_threshold]
    candidates.sort(key=lambda r: r["ndcg@5"])
    return candidates[:count]


def build_gap_cases(gap_queries: list[dict], search_fn, judgments: dict, item_lookup: dict) -> list[dict]:
    """
    For each gap query, pair the ground-truth best item (positive) against
    the model's own current top wrong answer (hard negative) — real
    retriever error, not a synthetic guess.
    """
    cases = []
    for gq in gap_queries:
        qid = gq["query_id"]

        # Ground-truth best item for this query, across whichever restaurant(s) it's judged in.
        best = None  # (relevance, restaurant_id, item_name)
        for (rid, q2), item_rels in judgments.items():
            if q2 != qid:
                continue
            for name, rel in item_rels.items():
                if best is None or rel > best[0]:
                    best = (rel, rid, name)
        if best is None:
            continue
        _, pos_rid, pos_name = best
        pos_item = item_lookup.get((pos_rid, pos_name))
        if pos_item is None:
            continue

        # Model's own current top wrong answer for this query.
        ranked = search_fn(gq["query_text"])
        neg_item = None
        for r in ranked:
            rel = judgments.get((r["restaurant_id"], qid), {}).get(r["name"], 0)
            if rel == 0:
                neg_item = {"name": r["name"], "description": r["description"], "category": r["category"]}
                break
        if neg_item is None:
            continue

        cases.append({
            "gap_query_id": qid,
            "category_id": gq["category_id"],
            "original_query": gq["query_text"],
            "ndcg@5_before": gq["ndcg@5"],
            "positive_item": pos_item,
            "negative_item": neg_item,
        })
    return cases


# ── LLM rewording via `claude -p` ───────────────────────────────────────────

def _call_claude(prompt: str, model: str, cwd: Path) -> str:
    result = subprocess.run(
        ["claude", "-p", "--restricted", "--output-format", "json", "--model", model, prompt],
        capture_output=True, text=True, cwd=str(cwd), timeout=120,
    )
    payload = json.loads(result.stdout)
    return payload.get("result", "")


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def reword_queries(cases: list[dict], model: str) -> None:
    """Mutates each case in place, setting case['anchor']."""
    scratch_dir = Path(tempfile.gettempdir())
    lines = [
        "For each numbered case, a search failed to find the right restaurant menu",
        "item. Write ONE alternative search query with the SAME intent as the",
        "original but DIFFERENT wording (not a verbatim copy) — the kind of thing",
        "a different user might type for the same craving. Output ONLY a raw JSON",
        "object (no markdown fences, no prose) mapping each numeric id (as a",
        "string) to a single short lowercase query string.",
        "",
        "Cases:",
    ]
    for i, case in enumerate(cases):
        lines.append(f'{i}. Original query: "{case["original_query"]}" '
                     f'— should match: "{case["positive_item"]["name"]}"')
    prompt = "\n".join(lines)

    try:
        raw = _call_claude(prompt, model, scratch_dir)
        parsed = _parse_json_object(raw)
    except Exception as e:
        print(f"  [warn] LLM rewording failed ({e}); falling back to original query text")
        parsed = {}

    for i, case in enumerate(cases):
        case["anchor"] = parsed.get(str(i)) or case["original_query"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", type=Path, default=_DEFAULT_MODEL,
                        help=f"Model to diagnose (default: {_DEFAULT_MODEL})")
    parser.add_argument("--count", type=int, default=_DEFAULT_COUNT,
                        help=f"Number of worst queries to target (default: {_DEFAULT_COUNT})")
    parser.add_argument("--ndcg-threshold", type=float, default=_DEFAULT_NDCG_THRESHOLD,
                        help=f"Only consider queries scoring below this NDCG@5 (default: {_DEFAULT_NDCG_THRESHOLD})")
    parser.add_argument("--llm-model", default=_DEFAULT_LLM_MODEL)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()

    from sentence_transformers import SentenceTransformer

    print(f"Loading model '{args.model}'...", end=" ", flush=True)
    model = SentenceTransformer(str(args.model))
    print("done")

    print("Loading menus and building index...", end=" ", flush=True)
    restaurants, menus = load_data(judged_restaurant_ids())
    index = build_index(menus, restaurants, model)
    print(f"{sum(len(v) for v in index.values())} items")

    name_to_id = {v.get("name", k): k for k, v in restaurants.items()}

    def search_fn(query: str) -> list[dict]:
        raw = _sbert_search(query, restaurants, index, model)
        out = []
        for r in raw:
            rid = name_to_id.get(r["restaurant"], r["restaurant"])
            out.append({"restaurant_id": rid, "name": r["item"], **r})
        return out

    print(f"Diagnosing: finding the {args.count} worst queries (NDCG@5 < {args.ndcg_threshold})...")
    gap_queries = find_gap_queries(search_fn, args.count, args.ndcg_threshold)
    print(f"  {len(gap_queries)} gap queries found")
    for gq in gap_queries[:10]:
        print(f"    {gq['query_id']:8} ndcg@5={gq['ndcg@5']:.3f} [{gq['category_id']}] {gq['query_text']}")
    if len(gap_queries) > 10:
        print(f"    ... and {len(gap_queries) - 10} more")

    judgments = load_relevance()
    item_lookup = {(rid, item["name"]): item for rid, items in menus.items() for item in items}
    cases = build_gap_cases(gap_queries, search_fn, judgments, item_lookup)
    print(f"\n{len(cases)} cases have both a ground-truth item and a current wrong answer to contrast")

    print(f"Rewording via `claude -p` ({args.llm_model})...")
    reword_queries(cases, args.llm_model)

    triples = []
    for case in cases:
        triples.append({
            "anchor": case["anchor"],
            "positive": _item_text(case["positive_item"]),
            "negative": _item_text(case["negative_item"]),
            "source": "gap_fill",
            "gap_query_id": case["gap_query_id"],
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for t in triples:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(triples)} triples to {args.out}")
    print("Sample:")
    for t in triples[:5]:
        print(f'  ({t["gap_query_id"]}) "{t["anchor"]}" -> + {t["positive"][:50]!r} / - {t["negative"][:50]!r}')
