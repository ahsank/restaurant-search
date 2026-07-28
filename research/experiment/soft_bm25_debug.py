"""
Debug tool for Soft-BM25: shows per-token cosine similarities so you can see
exactly why an item scores high or low for a given query.

For each item the script prints:
  - The FMM phrase tokens produced from the item text.
  - For every query token: the top-k most similar item tokens with cosine
    scores, whether each passes the threshold, and the resulting soft-TF.
  - The final score under every combiner (bm25, plus, product, min).

Usage (from repo root):
    conda run -n search python research/experiment/soft_bm25_debug.py \\
        --vectors models/numberbatch-en.txt "shellfish pasta"

    # change threshold / show more neighbours
    conda run -n search python research/experiment/soft_bm25_debug.py \\
        --vectors models/numberbatch-en.txt --threshold 0.4 --top-k 8 "crab noodles"
"""

import argparse
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np

# ── allow importing from research/search/ ────────────────────────────────────
_REPO = Path(__file__).parents[2]
sys.path.insert(0, str(_REPO / "research" / "search"))
from soft_bm25_search import (
    PhraseTokenizer,
    VectorStore,
    load_conceptnet,
    _item_text,
    _DEFAULT_IDF,
)

# ── hardcoded items for experimentation ───────────────────────────────────────
# Add or edit items here to probe different queries.
ITEMS = [
    # ── Staple & Fancy — item under investigation ─────────────────────────
    {
        "restaurant": "Staple & Fancy",
        "name": "Pappardelle",
        "description": "Crab, brown butter, white wine, citrus, sea beans, pangrattato, bottarga.",
        "category": "Pasta",
        "menu_type": "dinner",
    },
    # ── Staple & Fancy — other pasta for contrast ─────────────────────────
    {
        "restaurant": "Staple & Fancy",
        "name": "Tagliatelle",
        "description": "Braised beef, San Marzano tomato, Parmigiano-Reggiano.",
        "category": "Pasta",
        "menu_type": "dinner",
    },
    # ── True positives: shellfish + pasta ────────────────────────────────
    {
        "restaurant": "Test Kitchen",
        "name": "Shrimp & Clam Bucatini",
        "description": "Calabrian chili, garlic, white wine, gremolata.",
        "category": "Pasta",
        "menu_type": "dinner",
    },
    {
        "restaurant": "Test Kitchen",
        "name": "CajunPasta",
        "description": "Pasta with a Cajun cream sauce, clams, salmon, cod, bell peppers, broccoli, Parmesan.",
        "category": "Pasta",
        "menu_type": "dinner",
    },
    # ── Shellfish but no pasta ────────────────────────────────────────────
    {
        "restaurant": "Test Kitchen",
        "name": "Grilled Oysters",
        "description": "Pacific oysters, mignonette, lemon, hot sauce.",
        "category": "Seafood",
        "menu_type": "dinner",
    },
    # ── Pasta but no shellfish ────────────────────────────────────────────
    {
        "restaurant": "Test Kitchen",
        "name": "Cacio e Pepe",
        "description": "Tonnarelli, pecorino romano, black pepper.",
        "category": "Pasta",
        "menu_type": "dinner",
    },
]

# ── BM25 defaults (match soft_bm25_search.py) ────────────────────────────────
K1 = 1.5
B  = 0.75


def _unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    return v / norm if norm > 1e-9 else v


def _score_item_debug(
    query_tokens: list[str],
    query_vecs: list[np.ndarray | None],
    tokens: list[str],
    vecs: np.ndarray,
    threshold: float,
    top_k: int,
    avgdl: float,
    idf: dict[str, float],
) -> dict:
    """
    Run soft-BM25 scoring for one item and return detailed per-token stats.

    Returns a dict with:
      term_stats — list of {qt, soft_tf, top_matches: [{token, cos}]}
      scores     — {combiner: final_score}
    """
    dl = max(len(tokens), 1)
    term_stats = []
    bm25_terms: list[float] = []
    raw_stfs:   list[float] = []

    for qt, qv in zip(query_tokens, query_vecs):
        if qv is None:
            term_stats.append({"qt": qt, "soft_tf": None, "top_matches": []})
            continue

        if vecs.shape[0] == 0:
            stf = 0.0
            top_matches = []
        else:
            sims = vecs @ qv            # (n_item_tokens,)
            sorted_idx = np.argsort(sims)[::-1][:top_k]
            top_matches = [{"token": tokens[i], "cos": float(sims[i])} for i in sorted_idx]
            max_sim = min(1.0, float(sims.max()))
            stf = max_sim if max_sim >= threshold else 0.0

        term_stats.append({"qt": qt, "soft_tf": stf, "top_matches": top_matches})
        raw_stfs.append(stf)

        if stf > 0.0:
            tf_norm = stf * (K1 + 1) / (stf + K1 * (1 - B + B * dl / avgdl))
            bm25_terms.append(idf.get(qt, _DEFAULT_IDF) * tf_norm)

    # product / min need all raw stfs
    if raw_stfs and all(s > 0.0 for s in raw_stfs):
        prod_score = 1.0
        for s in raw_stfs:
            prod_score *= s
        min_score = min(raw_stfs)
    else:
        prod_score = 0.0
        min_score  = 0.0

    scores = {
        "bm25":    sum(bm25_terms),
        "plus":    sum(raw_stfs),
        "product": prod_score,
        "min":     min_score,
    }

    return {"term_stats": term_stats, "scores": scores}


def main():
    parser = argparse.ArgumentParser(
        description="Debug Soft-BM25 per-token cosine similarities"
    )
    parser.add_argument(
        "query", nargs="*", default=["shellfish", "pasta"],
        help="Query terms (default: shellfish pasta)",
    )
    parser.add_argument(
        "--vectors", default=str(_REPO / "models" / "numberbatch-en.txt"),
        help="Path to ConceptNet Numberbatch vectors (default: models/numberbatch-en.txt)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5,
        help="Soft-TF threshold (default: 0.5)",
    )
    parser.add_argument(
        "--top-k", type=int, default=5,
        help="How many top item-token matches to show per query term (default: 5)",
    )
    args = parser.parse_args()

    query = " ".join(args.query)
    print(f"\nQuery: '{query}'")
    print(f"Threshold: {args.threshold}  |  Top-k neighbours shown: {args.top_k}")
    print(f"Vectors: {args.vectors}\n")

    # ── load vectors ──────────────────────────────────────────────────────────
    print("Loading ConceptNet vectors …", end=" ", flush=True)
    raw_vecs, phrase_vocab = load_conceptnet(args.vectors)
    print(f"{len(raw_vecs):,} entries loaded")

    tokenizer = PhraseTokenizer(phrase_vocab)
    vs        = VectorStore(raw_vecs)

    # ── tokenise query ────────────────────────────────────────────────────────
    query_tokens = tokenizer.tokenize(query)
    query_vecs   = [vs.lookup(t) for t in query_tokens]

    print(f"\nQuery tokens:  {query_tokens}")
    missing = [t for t, v in zip(query_tokens, query_vecs) if v is None]
    if missing:
        print(f"  ⚠ No vector for: {missing}")

    # ── build a tiny fake index to get IDF + avgdl over ITEMS only ───────────
    doc_freq: dict[str, int] = {}
    total_tokens = 0
    item_token_data: list[tuple[list[str], np.ndarray]] = []

    for item in ITEMS:
        tokens = tokenizer.tokenize(_item_text(item))
        vecs_list = [(t, vs.lookup(t)) for t in tokens]
        pairs = [(t, v) for t, v in vecs_list if v is not None]
        for t in {t for t, _ in pairs}:
            doc_freq[t] = doc_freq.get(t, 0) + 1
        vmat = np.stack([v for _, v in pairs]) if pairs else np.zeros((0, 1), dtype=np.float32)
        item_token_data.append(([t for t, _ in pairs], vmat))
        total_tokens += len(pairs)

    n = len(ITEMS)
    idf = {
        t: math.log((n - df + 0.5) / (df + 0.5) + 1)
        for t, df in doc_freq.items()
    }
    avgdl = total_tokens / max(n, 1)

    # ── score and print ───────────────────────────────────────────────────────
    results = []
    for item, (tokens, vmat) in zip(ITEMS, item_token_data):
        debug = _score_item_debug(
            query_tokens, query_vecs,
            tokens, vmat,
            args.threshold, args.top_k,
            avgdl, idf,
        )
        results.append((item, tokens, debug))

    # sort by plus score descending for display order
    results.sort(key=lambda r: r[2]["scores"]["plus"], reverse=True)

    sep = "─" * 72

    for item, tokens, debug in results:
        label = f"{item['restaurant']} | {item['name']}"
        text  = _item_text(item)
        print(f"\n{'='*72}")
        print(f"  {label}")
        print(f"  text : {text}")
        print(f"  tokens ({len(tokens)}): {tokens}")
        print()

        for ts in debug["term_stats"]:
            qt = ts["qt"]
            stf = ts["soft_tf"]
            if stf is None:
                print(f"  Query term '{qt}':  NO VECTOR — skipped")
                continue

            passed = stf > 0.0
            print(f"  Query term '{qt}'  →  soft_tf = {stf:.4f}  ({'PASS' if passed else 'FAIL threshold'})")
            for m in ts["top_matches"]:
                flag = "✓" if m["cos"] >= args.threshold else "✗"
                print(f"      {flag} cos={m['cos']:+.4f}  '{m['token']}'")

        s = debug["scores"]
        print(f"\n  Scores:  bm25={s['bm25']:.4f}  plus={s['plus']:.4f}"
              f"  product={s['product']:.4f}  min={s['min']:.4f}")

    print(f"\n{'='*72}")
    print(f"Summary (sorted by 'plus' score)\n{'─'*72}")
    print(f"  {'Item':<45} {'plus':>6}  {'bm25':>6}  {'product':>7}  {'min':>6}")
    print(f"  {'─'*45} {'─'*6}  {'─'*6}  {'─'*7}  {'─'*6}")
    for item, _, debug in results:
        s = debug["scores"]
        label = f"{item['restaurant']} | {item['name']}"
        print(f"  {label:<45} {s['plus']:>6.4f}  {s['bm25']:>6.4f}  {s['product']:>7.4f}  {s['min']:>6.4f}")


if __name__ == "__main__":
    main()
