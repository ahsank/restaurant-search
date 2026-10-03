# Search Approach Benchmark Results

Snapshot comparison of the search engines implemented so far, run against the
full 209-query benchmark (`data/queries/`): 199 queries with judgments, 1,494
relevance labels, 8 restaurants, 795 items. Every row below was re-run in one
environment on this dataset. For method design details and trade-off
discussion, see [`APPROACHES.md`](APPROACHES.md).

Reproduce any row with:
```bash
python research/search/evaluate.py --engine <name> [options]
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
| `crossencoder` (ms-marco-MiniLM-L6-v2) | Cross-encoder — query and item read together in one forward pass, scored for every item (no first-stage retriever) | None (pretrained on MS MARCO); finetuned variants in Approach 6 | Medium |

`soft_bm25` config used below: `--combiner plus --spell-correct` (best measured
configuration; `plus` gives OR-with-partial-credit semantics, spell-correct
fixes queries like "tiramisou" → "tiramisu" before lookup).

Finetuned models (Approach 5 bi-encoders, Approach 6 finetuned
cross-encoders) are covered in `APPROACHES.md`, not here. This page compares
off-the-shelf engines.

---

## Overall results

| Engine | NDCG@5 | Recall@10 | MRR |
|---|---|---|---|
| `text` (baseline) | 0.4252 | 0.4589 | 0.4413 |
| `enhanced` (thesaurus) | 0.5254 | 0.5366 | 0.5615 |
| `filtered` | 0.5122 | 0.5153 | 0.5364 |
| `soft_bm25` (plus + spell-correct) | 0.5258 | 0.5422 | 0.6700 |
| `sbert` all-MiniLM-L6-v2 | 0.5288 | 0.5115 | 0.6561 |
| `sbert` all-mpnet-base-v2 | 0.5334 | 0.5029 | 0.6806 |
| `colbert` colbertv2.0 | 0.6067 | 0.5895 | 0.7255 |
| **`crossencoder` ms-marco-MiniLM-L6-v2** | **0.6261** | **0.6185** | **0.7714** |

**The cross-encoder is the clear winner**, ahead of ColBERT on every metric
(+0.019 NDCG@5, +0.029 Recall@10, +0.046 MRR). ColBERT is still the best
engine that can precompute item vectors. The cross-encoder has to run once
per (query, item), about 4 s per query over all 795 items on CPU, so in
production it would rerank a ColBERT top-K.

Behind those two, the middle tier is now nearly a tie at NDCG@5 ≈ 0.51–0.53:
`enhanced`, `filtered`, `soft_bm25` and both SBERT models. The hand-written
thesaurus (`enhanced`) still matches the off-the-shelf SBERT models on NDCG@5
with zero ML, though it trails them on MRR.

---

## By difficulty

| Engine | Easy NDCG@5 | Medium NDCG@5 | Hard NDCG@5 |
|---|---|---|---|
| `text` | 0.582 | 0.220 | 0.131 |
| `enhanced` | 0.684 | 0.345 | 0.170 |
| `filtered` | 0.685 | 0.312 | 0.131 |
| `soft_bm25` | 0.611 | 0.414 | **0.365** |
| `sbert` MiniLM | 0.621 | 0.481 | 0.197 |
| `sbert` mpnet | 0.624 | 0.454 | 0.278 |
| `colbert` | 0.728 | 0.505 | 0.254 |
| `crossencoder` | **0.734** | **0.528** | 0.329 |

(n = 125 Easy, 55 Medium, 29 Hard.)

Soft-BM25 is still the strongest off-the-shelf engine on **Hard** queries.
Its explicit AND-across-terms, phrase detection and spell correction help most
when queries are adversarial (misspellings, indirect phrasing). The
cross-encoder narrows that gap (0.329 vs. ColBERT's 0.254), and Approach 6's
finetuned cross-encoder reaches 0.375 on Hard, ahead of Soft-BM25.

---

## Category highlights

Categories where the gap between best and worst engine is largest (i.e. where
method choice matters most):

| Category | Weakest | Strongest | Notes |
|---|---|---|---|
| C05 Spelling variations | `text`/`enhanced`/`filtered` 0.067 | `colbert` 0.759 | Exact-match approaches fail completely on misspellings; subword-level models (ColBERT, cross-encoder 0.729) and spell-correction (Soft-BM25 0.548) close this gap |
| C17 Dessert varieties | `soft_bm25` 0.732 | `crossencoder` 0.967 | Small, low-ambiguity category — several methods score >0.9 |
| C02 Ingredient generalization | `text`/`filtered` 0.000 | `crossencoder` 0.394 / `colbert` 0.393 | Every method struggles — the hardest true generalization category |
| C01 Cuisine type inference | `text` 0.000 | `crossencoder` 0.438 / `sbert` mpnet 0.418 | Requires inferring cuisine from context, not keywords — favors dense models |
| C10 Multi-constraint compositional | Most engines 0.000 | `sbert` mpnet 0.169 | Universally weak; only 2 queries, needs a fundamentally different approach (e.g. LLM reader) |

**No method tested so far solves C01–C04, C08 or C10 well.** The
cross-encoder is the best or near-best on C01 and C02, but still under 0.45.
These categories require compositional or inferential reasoning beyond token-
or pair-level similarity. Training data aimed at them, or Approach 7 (LLM
reader), are the next candidates.

---

## Takeaways

1. **The off-the-shelf cross-encoder (Approach 6) is the best engine measured**: +0.019 NDCG@5 and +0.046 MRR over ColBERT, with no training. Its cost is query-time compute, so the practical setup is ColBERT retrieval plus cross-encoder reranking.
2. **ColBERT (Approach 4.5) is the best engine with precomputable item vectors**, +0.07 NDCG@5 or more over everything except the cross-encoder.
3. **A hand-written thesaurus is a surprisingly strong, nearly-free baseline** for a bounded domain like restaurant menus. `enhanced` ties both SBERT models on NDCG@5.
4. **Soft-BM25 still wins on Hard queries** among untrained engines. It's worth keeping as a component (e.g. hybrid retrieval or a fallback).
5. **Bigger SBERT model ≠ meaningfully better.** mpnet-base-v2 beats MiniLM-L6-v2 by only +0.005 NDCG@5 and loses on Recall@10. That confirms the single-pooled-vector architecture is the bottleneck, not model capacity.
6. **The remaining hard categories (C01–C04, C08, C10) need more than better similarity.** Queries like "Tex-Mex combination plate" or "gluten free seafood under $30" call for compositional reasoning.

### Change since the previous snapshot

The previous snapshot used a 204-query, 7-restaurant benchmark (1,081 labels,
653 items). Adding queries and Anthony's HomePort judgments raised every
engine's NDCG@5 by 0.007–0.031. The previous NDCG@5 values were: text 0.4179,
enhanced 0.5115, filtered 0.4965, soft_bm25 0.5063, MiniLM 0.4983, mpnet
0.5033, ColBERT 0.5931. The ranking is unchanged except that the cross-encoder
is new at the top and `enhanced` no longer leads the middle tier.

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

# Cross-encoder, scoring every item (~13.5 min on a 4-core CPU; ~1 min on a GPU)
python research/search/evaluate.py --engine crossencoder
```

Useful flags on any of the above:
- `--verbose` — print per-query NDCG/Recall/MRR as it runs, not just the aggregate report
- `--category C05` — restrict to one query category (see `data/queries/README.md` for the C01–C25 list)
- `--difficulty Hard` — restrict to one difficulty tier

`models/numberbatch-en.txt` (ConceptNet Numberbatch, required only for
`soft_bm25`) is gitignored — download it per the instructions in
`research/COMMANDS.md` if it's missing locally. `sbert`, `colbert` and
`crossencoder` download their models automatically on first run (cached under
`~/.cache/huggingface` afterward, no repeat download).

Numbers will shift slightly if `data/menus/` or `data/queries/relevance_*.csv`
change — this snapshot reflects the 8-restaurant, 795-item, 1,494-judgment
benchmark described at the top of this document. Re-run all eight commands
and update this file's tables if you want a fresh snapshot after a data or
algorithm change.
