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

Item text is lib.data.item_text() (name. description. category) — the
same format as the positives/negatives in the Approach 5 triples the model
was finetuned on.

Usage:
    python research/search/crossencoder_search.py seafood italian
    python research/search/crossencoder_search.py --benchmark-only spicy noodles
    python research/search/crossencoder_search.py --model cross-encoder/ms-marco-MiniLM-L6-v2 oyster

Equivalent via the shared --engine dispatcher (used by evaluate.py):
    python research/search/evaluate.py --engine crossencoder --model models/crossencoder-synthetic-plus-gapfill

Score cache (--scores FILE): scoring every item for every benchmark query
takes ~13.5 min on CPU, so evaluate.py can store the full query x item score
matrix as a text file and replay it. The file records a fingerprint of the
menus and queries.csv (not the relevance labels); if either changed, the file
is rebuilt from scratch, otherwise evaluation is a lookup:
    python research/search/evaluate.py --engine crossencoder \
        --scores research/results/crossencoder/ms-marco-MiniLM-L6-v2.scores.tsv
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import benchmark_fingerprint, item_text, load_data, judged_restaurant_ids, restaurant_scope_cli_args

_ROOT = Path(__file__).parents[2]
_DEFAULT_MODEL = _ROOT / "models" / "crossencoder-synthetic-plus-gapfill"
STOCK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
SCORES_FORMAT = 1


def cli_args() -> argparse.ArgumentParser:
    """--scores flag fragment; engines.build_arg_parser() adds it for --engine crossencoder."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--scores", type=Path,
        help="Score cache (text TSV, safe to commit): replay scores from this file, or "
             "compute every benchmark query x item and write it if missing or stale "
             "(menus or queries.csv changed). Relabeling never invalidates it.",
    )
    return parser


def build_index(menus: dict, restaurants: dict) -> list[tuple[str, dict, str]]:
    """Flatten every item into (restaurant_id, item, item_text). Nothing to encode up front."""
    return [
        (rid, item, item_text(item))
        for rid, items in menus.items()
        for item in items
    ]


def search(
    query: str,
    restaurants: dict,
    index: list[tuple[str, dict, str]],
    model,
    batch_size: int = 128,
) -> list[dict]:
    """Score (query, item_text) for every indexed item and sort best-first."""
    scores = model.predict(
        [(query, text) for _, _, text in index],
        batch_size=batch_size,
        show_progress_bar=False,
    )
    return rank(restaurants, index, [float(s) for s in scores])


def rank(restaurants: dict, index: list[tuple[str, dict, str]], scores: list[float]) -> list[dict]:
    """Result dicts for index entries with the given scores, best-first (stable on ties)."""
    scored: list[tuple[float, dict]] = []
    for (rid, item, _), score in zip(index, scores):
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


# ---------------------------------------------------------------------------
# Score cache: one text file with every benchmark query x item score
# ---------------------------------------------------------------------------
#
#   # crossencoder-scores format=1
#   # model: cross-encoder/ms-marco-MiniLM-L6-v2
#   # fingerprint: 3f2a...           (lib.data.benchmark_fingerprint)
#   query_id <TAB> query_text <TAB> <restaurant_id>|<item name> <TAB> ...
#   C01-01   <TAB> Mexican food... <TAB> -3.12345 <TAB> ...
#
# Columns follow build_index() order, so replaying sorts exactly like search().

def _column(entry: tuple[str, dict, str]) -> str:
    rid, item, _ = entry
    return f"{rid}|{item['name']}"


def write_scores(path: Path, model_name: str, fingerprint: str, index, queries: list[dict], model) -> None:
    """Score every query against every index entry and write the TSV cache."""
    import time
    path.parent.mkdir(parents=True, exist_ok=True)
    texts = [text for _, _, text in index]
    t0 = time.time()
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# crossencoder-scores format={SCORES_FORMAT}\n")
        f.write(f"# model: {model_name}\n")
        f.write(f"# fingerprint: {fingerprint}\n")
        f.write("\t".join(["query_id", "query_text"] + [_column(e) for e in index]) + "\n")
        for i, q in enumerate(queries, 1):
            scores = model.predict([(q["query_text"], t) for t in texts], batch_size=128, show_progress_bar=False)
            f.write("\t".join([q["query_id"], q["query_text"]] + [f"{float(s):.5f}" for s in scores]) + "\n")
            if i % 20 == 0 or i == len(queries):
                print(f"  scored {i}/{len(queries)} queries ({time.time() - t0:.0f}s)", flush=True)


def read_scores(path: Path, model_name: str, fingerprint: str, index) -> dict[str, list[float]] | None:
    """{query_text: scores in index order}, or None if the file is missing or stale."""
    if not path.exists():
        print(f"Score cache {path} not found; it will be created.")
        return None
    with open(path, encoding="utf-8") as f:
        meta = {}
        line = f.readline()
        while line.startswith("#"):
            if ":" in line:
                k, _, v = line[1:].partition(":")
                meta[k.strip()] = v.strip()
            line = f.readline()
        columns = line.rstrip("\n").split("\t")[2:]
        problems = []
        if meta.get("model") != model_name:
            problems.append(f"model {meta.get('model')!r} != {model_name!r}")
        if meta.get("fingerprint") != fingerprint:
            problems.append("menus or queries.csv changed since it was written")
        if columns != [_column(e) for e in index]:
            problems.append("menu item columns differ")
        if problems:
            print(f"Score cache {path} is stale ({'; '.join(problems)}); rebuilding from scratch.")
            return None
        rows = {}
        for line in f:
            parts = line.rstrip("\n").split("\t")
            rows[parts[1]] = [float(x) for x in parts[2:]]
    return rows


def cached_search_fn(path: Path, model_name: str, restaurants: dict, menus: dict, load_model):
    """
    search_fn(query) backed by the score cache at path. Builds (or rebuilds) the
    cache over every benchmark query when needed; queries not in the cache
    (ad-hoc searches) fall back to live scoring with load_model().
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from evaluate import load_queries

    index = build_index(menus, restaurants)
    fingerprint = benchmark_fingerprint(set(menus))
    rows = read_scores(path, model_name, fingerprint, index)
    model = None
    if rows is None:
        queries = load_queries()
        model = load_model()
        print(f"Scoring {len(queries)} queries x {len(index)} items into {path}...")
        write_scores(path, model_name, fingerprint, index, queries, model)
        rows = read_scores(path, model_name, fingerprint, index)
    print(f"Replaying cross-encoder scores from {path} ({len(rows)} queries)")

    def _search(query: str) -> list[dict]:
        nonlocal model
        if query in rows:
            return rank(restaurants, index, rows[query])
        if model is None:
            model = load_model()
        return search(query, restaurants, index, model)
    return _search


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

    from sentence_transformers.cross_encoder import CrossEncoder
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
