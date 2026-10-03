# Search Approach Benchmark Results

Snapshot comparison of every search engine implemented so far, run against the
full 204-query benchmark (`data/queries/`, 194 queries with judgments, 1,081
relevance labels, 7 restaurants, 653 items). For method design details and
trade-off discussion, see [`APPROACHES.md`](APPROACHES.md).

Reproduce any row with:
```bash
python research/search/evaluate.py --engine <name> [options]
```

---

## Update — current benchmark (8 restaurants) and Approach 6

The rest of this page is a snapshot from the 204-query, 7-restaurant
benchmark. Since then, the benchmark has grown to 209 queries, 199 of them
judged, with 1,494 relevance labels and 795 items. Anthony's HomePort now has
judgments too, which shifted every engine's numbers. Re-run on the current
benchmark, in one environment:

| Engine | NDCG@5 | Recall@10 | MRR | Easy | Medium | Hard |
|---|---|---|---|---|---|---|
| `sbert` all-MiniLM-L6-v2 | 0.5288 | 0.5115 | 0.6561 | 0.621 | 0.481 | 0.197 |
| `colbert` colbertv2.0 | 0.6067 | 0.5895 | 0.7255 | 0.728 | 0.505 | 0.254 |
| **`crossencoder` ms-marco-MiniLM-L6-v2 (stock, scores every item)** | **0.6261** | **0.6185** | **0.7714** | 0.734 | **0.528** | 0.329 |
| `crossencoder` finetuned, synthetic only | 0.6258 | 0.6097 | 0.7476 | 0.732 | 0.511 | 0.370 |
| `crossencoder` finetuned, synthetic + gap-fill | 0.6272 | 0.6139 | 0.7405 | **0.739** | 0.500 | **0.375** |

(Easy/Medium/Hard columns are NDCG@5.)

**The stock cross-encoder (Approach 6) is now the best engine measured**,
ahead of ColBERT on every overall metric and by the widest margin on Hard
queries, with no training. Finetuning it on Approach 5's synthetic triples
leaves NDCG@5 flat: Hard queries improve while Medium queries and MRR drop.
See Approach 6 in [`APPROACHES.md`](APPROACHES.md) for the training setup,
leakage analysis and per-category notes.

```bash
python research/search/evaluate.py --engine crossencoder
python research/search/evaluate.py --engine crossencoder --model models/crossencoder-synthetic-plus-gapfill
```

---

## Method summary

| Engine | Technique | Training | Complexity |
|---|---|---|---|
| `text` | Exact keyword substring match (baseline) | None | Trivial |
| `enhanced` | Keyword match + hand-written thesaurus expansion | None | Low |
| `filtered` | `enhanced` + restaurant-context filtering | None | Low |
| `soft_bm25` | Phrase-aware tokenisation (FMM) + MaxSim soft term frequency + BM25 saturation, using static ConceptNet Numberbatch vectors | None (pretrained vectors) | Medium |
| `sbert` (MiniLM-L6-v2) | Bi-encoder — whole item text encoded as one sentence vector, cosine similarity | None (pretrained) | Medium |
| `sbert` (mpnet-base-v2) | Same bi-encoder architecture, larger base model | None (pretrained) | Medium |
| `colbert` (colbertv2.0) | Late interaction — one trained contextual vector per token, MaxSim scoring | None (pretrained, but the checkpoint itself was contrastively fine-tuned on MS MARCO) | Medium |

`soft_bm25` config used below: `--combiner plus --spell-correct` (best measured
configuration; `plus` gives OR-with-partial-credit semantics, spell-correct
fixes queries like "tiramisou" → "tiramisu" before lookup).

---

## Overall results

| Engine | NDCG@5 | Recall@10 | MRR |
|---|---|---|---|
| `text` (baseline) | 0.4179 | 0.4613 | 0.4288 |
| `enhanced` (thesaurus) | **0.5115** | 0.5369 | 0.5381 |
| `filtered` | 0.4965 | 0.5179 | 0.5120 |
| `soft_bm25` (plus + spell-correct) | 0.5063 | 0.5684 | 0.6368 |
| `sbert` all-MiniLM-L6-v2 | 0.4983 | 0.5217 | 0.6169 |
| `sbert` all-mpnet-base-v2 | 0.5033 | 0.5113 | 0.6358 |
| **`colbert` colbertv2.0** | **0.5931** | **0.6121** | **0.6970** |

**ColBERT is the clear winner** — +8 to +18 NDCG points over every other
approach, including both SBERT variants and Soft-BM25. Notably, the
hand-written thesaurus (`enhanced`) — zero ML, zero dependencies — is
competitive with or beats both off-the-shelf SBERT models and Soft-BM25 on
NDCG@5, though it loses on Recall@10 and MRR. This says more about the
benchmark's food vocabulary being well covered by the thesaurus than it does
about SBERT/Soft-BM25 being weak; a broader or more adversarial query set
would likely favor the embedding-based approaches more.

---

## By difficulty

| Engine | Easy NDCG@5 | Medium NDCG@5 | Hard NDCG@5 |
|---|---|---|---|
| `text` | 0.580 | 0.224 | 0.091 |
| `enhanced` | 0.684 | 0.320 | 0.130 |
| `filtered` | 0.676 | 0.303 | 0.091 |
| `soft_bm25` | 0.591 | 0.404 | **0.338** |
| `sbert` MiniLM | 0.608 | 0.417 | 0.169 |
| `sbert` mpnet | 0.609 | 0.400 | 0.243 |
| `colbert` | **0.737** | **0.465** | 0.207 |

Soft-BM25 is the strongest engine specifically on **Hard** queries — its
explicit AND-across-terms and phrase detection help most when queries are
adversarial (misspellings, indirect phrasing). ColBERT dominates Easy/Medium
but doesn't carry that advantage into Hard queries as cleanly.

---

## Category highlights

Categories where the gap between best and worst engine is largest (i.e. where
method choice matters most):

| Category | Weakest | Strongest | Notes |
|---|---|---|---|
| C05 Spelling variations | `text`/`filtered` 0.067 | `colbert` 0.793 | Exact-match approaches fail completely on misspellings; spell-correction (Soft-BM25) and subword-level models (ColBERT) both close this gap |
| C17 Dessert varieties | `soft_bm25` 0.732 | `sbert` MiniLM 0.960 | Small, low-ambiguity category — several methods score >0.9 |
| C02 Ingredient generalization | `text`/`filtered` 0.000 | `sbert` mpnet 0.236 | Every method struggles — the hardest true generalization category |
| C01 Cuisine type inference | `text`/`filtered` 0.000–0.125 | `sbert` mpnet 0.374 | Requires inferring cuisine from context, not keywords — favors dense embeddings |
| C10 Multi-constraint compositional | Most engines 0.000–0.117 | — | Universally weak; only 2 queries, needs a fundamentally different approach (cross-encoder or LLM reader) |

**No method tested so far solves C01–C04 or C10 well.** These require
compositional or inferential reasoning beyond token-level similarity —
per `APPROACHES.md`, Approach 6 (cross-encoder, now trainable on the 1,081
real relevance judgments already collected) or Approach 7 (local LLM reader)
are the next candidates for these categories specifically.

---

## Takeaways

1. **ColBERT (Approach 4.5) is the best off-the-shelf option** — no training required, +8–18 NDCG points over every alternative tested.
2. **A hand-written thesaurus is a surprisingly strong, nearly-free baseline** for a bounded domain like restaurant menus — don't skip it when scoping a new project.
3. **Soft-BM25 uniquely wins on Hard queries** — worth keeping as a component (e.g. hybrid retrieval or a fallback) even though ColBERT wins overall.
4. **Bigger SBERT model ≠ meaningfully better** — mpnet-base-v2 barely beats MiniLM-L6-v2 (+0.005 NDCG@5), confirming the SBERT bi-encoder architecture (single pooled vector per item) is the bottleneck, not model capacity. This is why ColBERT (token-level, not sentence-level) wins by a wide margin instead.
5. **The remaining hard categories (C01–C04, C10) need a different architecture entirely** — token/sentence similarity, however well-trained, isn't sufficient for compositional or inferential queries like "Tex-Mex combination plate" or "gluten free seafood under $30."

---

## How to re-run this benchmark

All numbers above come from `research/search/evaluate.py`. Run from the repo root, with the `search` conda environment active (or prefix commands with `conda run -n search`):

```bash
# baseline keyword search
python research/search/evaluate.py --engine text

# thesaurus-expanded keyword search
python research/search/evaluate.py --engine enhanced
python research/search/evaluate.py --engine filtered

# Soft-BM25 — the config used in this doc
python research/search/evaluate.py --engine soft_bm25 \
    --vectors models/numberbatch-en.txt --combiner plus --spell-correct

# SBERT bi-encoder — either model
python research/search/evaluate.py --engine sbert --model all-MiniLM-L6-v2
python research/search/evaluate.py --engine sbert --model all-mpnet-base-v2

# ColBERT late interaction
python research/search/evaluate.py --engine colbert
```

Useful flags on any of the above:
- `--verbose` — print per-query NDCG/Recall/MRR as it runs, not just the aggregate report
- `--category C05` — restrict to one query category (see `data/queries/README.md` for the C01–C23 list)
- `--difficulty Hard` — restrict to one difficulty tier

`models/numberbatch-en.txt` (ConceptNet Numberbatch, required only for
`soft_bm25`) is gitignored — download it per the instructions at the top of
`research/search/soft_bm25_search.py` if it's missing locally. `sbert` and
`colbert` download their models automatically on first run (cached under
`~/.cache/huggingface` afterward, no repeat download).

Numbers will shift slightly if `data/menus/` or `data/queries/relevance_*.csv`
change — this snapshot reflects the dataset as of the 7-restaurant, 653-item,
1,081-judgment benchmark described at the top of this document. Re-run all
seven commands and update this file's tables if you want a fresh snapshot
after a data or algorithm change.
