"""
Approach 5 data generation: build (anchor, positive, hard_negative) triples for
finetuning a bi-encoder (research/train/finetune_biencoder.py).

Two negative sources, both free of any LLM cost — see the "Approach 5" section
of research/APPROACHES.md for the reasoning behind why negative quality (not
label volume) is the actual blocker for this dataset size:

1. Relevance-graded pairs (`_csv_pairs`) — reads data/queries/relevance_*.csv
   directly. For each query, a relevance=2 item is the positive; a
   same-restaurant, same-category item with lower judged relevance (or
   unlisted, i.e. implicit 0) is the hard negative. Fully deterministic, no
   model required.

2. Retriever-mined negatives (`_retriever_mined`) — sentence_transformers.
   util.mine_hard_negatives() embeds every judged (query, positive) pair and
   every candidate item with a pretrained bi-encoder, then samples
   close-but-wrong items as negatives. This approximates "the model's own
   mistakes" without a full retrieval pass over the benchmark. Mined
   negatives that happen to equal another judged-relevant item for the same
   query are dropped afterward — mine_hard_negatives only knows about the
   single positive on the row it's given, not every other judged item for
   that query.

Train/test leakage: evaluate.py always scores against the full data/queries/
benchmark, so building triples from every judged query and then evaluating a
finetuned model against those same queries would inflate NDCG (the model can
partially memorize eval queries during training). To keep the eventual
benchmark comparison honest, `--held-out-fraction` of queries per category are
excluded from triple generation and their ids written to `--held-out-file`;
pass that file to evaluate.py's `--query-ids-file` to score only on queries no
triple was built from.

Usage:
    python research/data_gen/mine_hard_negatives.py
    python research/data_gen/mine_hard_negatives.py --skip-retriever-mining
    python research/data_gen/mine_hard_negatives.py --mining-model all-mpnet-base-v2 --num-negatives 5

Output:
    research/data_gen/triples.jsonl (or --out) — JSONL of
        {"anchor", "positive", "negative", "source"} rows
    research/data_gen/held_out_query_ids.txt (or --held-out-file) — query_ids
        excluded from training, one per line
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "research"))
from lib.data import item_text, load_data, judged_restaurant_ids

sys.path.insert(0, str(_ROOT / "research" / "search"))
from evaluate import load_queries, load_relevance

_DEFAULT_OUT = Path(__file__).parent / "triples.jsonl"
_DEFAULT_HELD_OUT = Path(__file__).parent / "held_out_query_ids.txt"
_DEFAULT_MINING_MODEL = "all-MiniLM-L6-v2"


def split_query_ids(
    queries_by_id: dict,
    held_out_fraction: float,
    seed: int,
) -> tuple[set[str], set[str]]:
    """
    Split query_ids into (train, held_out), stratified by category_id so every
    category is represented in both splits (rather than e.g. all of C25's 2
    queries landing in one side by chance).

    This split exists to prevent train/test leakage: evaluate.py always scores
    against the full data/queries/ benchmark, and training triples are mined
    from the same relevance_*.csv judgments. Without holding out queries, a
    finetuned model can partially memorize benchmark queries during training
    and then score against those same queries at eval time — inflating NDCG
    far above what generalization to new queries would actually look like.
    Held-out query_ids are written to a file so evaluate.py can score
    exclusively on queries the model never saw a triple for.
    """
    by_category: dict[str, list[str]] = defaultdict(list)
    for qid, q in queries_by_id.items():
        by_category[q["category_id"]].append(qid)

    rng = random.Random(seed)
    held_out: set[str] = set()
    for qids in by_category.values():
        qids = sorted(qids)
        rng.shuffle(qids)
        n_held = max(1, round(len(qids) * held_out_fraction))
        held_out.update(qids[:n_held])

    train = set(queries_by_id) - held_out
    return train, held_out


# ── Method 1: relevance-graded pairs (no model required) ───────────────────

def mine_csv_pairs(
    menus: dict,
    queries_by_id: dict,
    judgments: dict,
    negatives_per_positive: int,
) -> list[dict]:
    item_lookup = {
        (rid, item["name"]): item
        for rid, items in menus.items()
        for item in items
    }

    triples: list[dict] = []
    for (rid, qid), item_rels in judgments.items():
        query = queries_by_id.get(qid)
        if query is None:
            continue
        restaurant_items = menus.get(rid, [])

        for name, rel in item_rels.items():
            if rel != 2:
                continue
            pos_item = item_lookup.get((rid, name))
            if pos_item is None:
                continue  # menu_item name in the CSV doesn't match the .md file

            same_category = [
                it for it in restaurant_items
                if it["category"] == pos_item["category"] and it["name"] != name
            ]
            # Prefer explicit relevance=1 negatives (closest — "related but
            # incomplete") over unlisted/implicit-0 same-category items.
            weak = [it for it in same_category if item_rels.get(it["name"], 0) == 1]
            unlisted = [it for it in same_category if it["name"] not in item_rels]

            for neg_item in (weak + unlisted)[:negatives_per_positive]:
                triples.append({
                    "anchor": query["query_text"],
                    "positive": item_text(pos_item),
                    "negative": item_text(neg_item),
                    "source": "csv_pairs",
                })
    return triples


# ── Method 2: retriever-mined negatives ─────────────────────────────────────

def mine_retriever_negatives(
    menus: dict,
    queries_by_id: dict,
    judgments: dict,
    mining_model_name: str,
    num_negatives: int,
    relative_margin: float,
) -> list[dict]:
    from datasets import Dataset
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import mine_hard_negatives

    item_lookup = {
        (rid, item["name"]): item
        for rid, items in menus.items()
        for item in items
    }

    anchors: list[str] = []
    positives: list[str] = []
    relevant_texts_by_query: dict[str, set[str]] = defaultdict(set)

    for (rid, qid), item_rels in judgments.items():
        query = queries_by_id.get(qid)
        if query is None:
            continue
        for name, rel in item_rels.items():
            if rel < 1:
                continue
            item = item_lookup.get((rid, name))
            if item is None:
                continue
            text = item_text(item)
            relevant_texts_by_query[query["query_text"]].add(text)
            anchors.append(query["query_text"])
            positives.append(text)

    if not anchors:
        return []

    dataset = Dataset.from_dict({"anchor": anchors, "positive": positives})
    corpus = sorted({item_text(it) for items in menus.values() for it in items})

    print(f"Loading mining model '{mining_model_name}'...", end=" ", flush=True)
    model = SentenceTransformer(mining_model_name)
    print("done")

    mined = mine_hard_negatives(
        dataset=dataset,
        model=model,
        corpus=corpus,
        num_negatives=num_negatives,
        relative_margin=relative_margin,
        sampling_strategy="top",
        output_format="triplet",
        batch_size=64,
        verbose=True,
    )

    triples: list[dict] = []
    for row in mined:
        if row["negative"] in relevant_texts_by_query.get(row["anchor"], ()):
            continue  # another judged-relevant item for this query, not a real negative
        triples.append({
            "anchor": row["anchor"],
            "positive": row["positive"],
            "negative": row["negative"],
            "source": "retriever_mined",
        })
    return triples


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT, help=f"Output JSONL path (default: {_DEFAULT_OUT})")
    parser.add_argument("--negatives-per-positive", type=int, default=2,
                        help="Max same-category hard negatives per relevance=2 positive (method 1, default: 2)")
    parser.add_argument("--mining-model", default=_DEFAULT_MINING_MODEL,
                        help=f"Bi-encoder used to embed+mine for method 2 (default: {_DEFAULT_MINING_MODEL})")
    parser.add_argument("--num-negatives", type=int, default=3,
                        help="Hard negatives per (query, positive) pair from method 2 (default: 3)")
    parser.add_argument("--relative-margin", type=float, default=0.05,
                        help="mine_hard_negatives relative_margin — a candidate must be at most this "
                             "fraction as similar to the anchor as the true positive (default: 0.05)")
    parser.add_argument("--skip-retriever-mining", action="store_true",
                        help="Only run method 1 (relevance-graded pairs) — fast, no model download")
    parser.add_argument("--held-out-fraction", type=float, default=0.2,
                        help="Fraction of queries per category excluded from training triples and "
                             "written to held-out-file, so evaluate.py can score on unseen queries "
                             "(default: 0.2)")
    parser.add_argument("--held-out-file", type=Path, default=_DEFAULT_HELD_OUT,
                        help=f"Where to write held-out query_ids, one per line (default: {_DEFAULT_HELD_OUT})")
    parser.add_argument("--seed", type=int, default=42, help="Held-out split seed (default: 42)")
    args = parser.parse_args()

    print("Loading benchmark data...", end=" ", flush=True)
    restaurants, menus = load_data(judged_restaurant_ids())
    queries_by_id = {q["query_id"]: q for q in load_queries()}
    judgments = load_relevance()
    print(f"{sum(len(v) for v in menus.values())} items, {len(queries_by_id)} queries, "
          f"{len(judgments)} judged (restaurant, query) pairs")

    train_qids, held_out_qids = split_query_ids(queries_by_id, args.held_out_fraction, args.seed)
    train_queries_by_id = {qid: q for qid, q in queries_by_id.items() if qid in train_qids}
    train_judgments = {(rid, qid): rels for (rid, qid), rels in judgments.items() if qid in train_qids}
    args.held_out_file.parent.mkdir(parents=True, exist_ok=True)
    args.held_out_file.write_text("\n".join(sorted(held_out_qids)) + "\n")
    print(f"Held out {len(held_out_qids)}/{len(queries_by_id)} queries (untouched by training data) "
          f"-> {args.held_out_file}")

    print("\nMethod 1 — relevance-graded pairs...")
    csv_triples = mine_csv_pairs(menus, train_queries_by_id, train_judgments, args.negatives_per_positive)
    print(f"  {len(csv_triples)} triples")

    retriever_triples: list[dict] = []
    if not args.skip_retriever_mining:
        print("\nMethod 2 — retriever-mined negatives...")
        retriever_triples = mine_retriever_negatives(
            menus, train_queries_by_id, train_judgments,
            args.mining_model, args.num_negatives, args.relative_margin,
        )
        print(f"  {len(retriever_triples)} triples")

    all_triples = csv_triples + retriever_triples
    # De-dupe identical (anchor, positive, negative) rows produced by both methods
    seen = set()
    deduped = []
    for t in all_triples:
        key = (t["anchor"], t["positive"], t["negative"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(t)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for t in deduped:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    n_queries = len({t["anchor"] for t in deduped})
    print(f"\nWrote {len(deduped)} triples ({len(all_triples) - len(deduped)} duplicates dropped) "
          f"covering {n_queries} distinct queries to {args.out}")
