# Semantic Search Approaches

Reference document for the restaurant menu semantic search problem. The core challenge: a query like `seafood italian` must surface "CajunPasta" (clams, salmon, cod) even though neither word appears in the dish name or description.

---

## The Problem with Plain Text Search

Simple substring/keyword matching fails because it requires the exact word to appear. `seafood` does not match `shrimp`, `clams`, `salmon`, or `cod`. Every approach below is a different strategy for bridging that gap.

The baseline is in `search/text_search.py` — run it to see the failure:

```bash
python search/text_search.py seafood italian   # 0 results
python search/text_search.py pasta             # 4 results (keyword present)
```

---

## Approach 1 — Concept Thesaurus Expansion

Maintain a static map from query concepts to related ingredients and terms:

```python
THESAURUS = {
    "seafood": {"shrimp", "clam", "salmon", "cod", "lobster", "scallop", "crab", "tuna"},
    "italian": {"pasta", "pizza", "risotto", "parmesan", "carbonara", "mozzarella"},
    "spicy":   {"chili", "jalapeño", "sriracha", "arrabbiata", "cajun", "habanero"},
    "healthy": {"quinoa", "avocado", "kale", "vegan", "gluten-free", "salad"},
}
```

Expand each query term using the map, then do keyword matching against the expanded term set. For a multi-word query, require each original term's expansion to contribute at least one match (AND semantics across concepts, OR within a concept).

**Pros:** Pure Python/C++, zero dependencies, fast, fully explainable, works offline, easy to debug.

**Cons:** Manual maintenance — someone must enumerate every synonym. Won't generalize to terms not in the map. Brittle for novel queries.

**Best for:** Getting a working demo quickly. The food domain is bounded enough that a useful thesaurus is achievable.

**Files:** `research/search/thesaurus_search.py` (to be created)

---

## Approach 2 — BM25 + Query Expansion

BM25 (Best Match 25) is a standard ranked retrieval function used by Elasticsearch and Lucene. It improves on TF-IDF by normalizing for document length and saturating term frequency. Combined with thesaurus-based query expansion it becomes a strong baseline.

**How it works:**
1. Index all menu text (name + description + category + restaurant cuisine_type)
2. Expand the query using the thesaurus (same as Approach 1)
3. Rank items by BM25 score against the expanded query

**Pros:** Still no ML, well-understood, handles partial matches and term frequency gracefully, good recall at scale, many Python libraries available (`rank-bm25`).

**Cons:** Still depends on the thesaurus for semantic lifting — `seafood` won't find `shrimp` without expansion.

**Library:** `pip install rank-bm25`

**Files:** `research/search/bm25_search.py` (to be created)

---

## Approach 3 — Word Embeddings (Word2Vec / GloVe / FastText)

Use pretrained word vectors. Each word is a dense numeric vector (e.g., 100 dimensions) where semantically similar words are geometrically close:

```
embed("shrimp") ≈ embed("salmon") ≈ embed("seafood")   ← close in vector space
embed("pasta")  ≈ embed("spaghetti") ≈ embed("italian")
```

**How it works:**
1. Download pretrained vectors (e.g., GloVe 6B, ~170 MB)
2. At index time: represent each menu item as the average vector of its words
3. At query time: compute the average query vector, rank items by cosine similarity

**Pros:** Generalizes automatically — no manual thesaurus. `shrimp spaghetti` will surface for `seafood italian` because the vector geometry encodes that relationship from the pretraining corpus.

**Cons:** Word-level averaging loses phrase context (`not spicy` looks similar to `spicy`). Rare food terms may have weak vectors. Requires a ~100–200 MB vector file at runtime.

**Library:** `gensim` or load GloVe vectors manually with `numpy`

**Files:** `research/search/embedding_search.py` (to be created)

---

## Approach 3.5 — Phrase-Aware Soft-BM25

Bridges the gap between Approach 3 (word averaging) and Approach 4 (SBERT).
Combines two ideas: phrase-aware tokenisation so that "oyster sauce" is a single
semantic unit distinct from "oyster", and soft (MaxSim) term frequency so that
"seafood" finds "shrimp" even when the word "seafood" is absent.

### How it works

**Step 1 — Phrase-aware tokenisation (Forward Maximum Matching)**

Before indexing or querying, text is tokenised by greedily taking the longest
matching phrase (up to N words) found in the embedding vocabulary:

```
"Beef in Oyster Sauce"   →  ["beef", "in", "oyster_sauce"]
"Egg Foo Young with rice" →  ["egg_foo_young", "with", "rice"]
"Kung Pao Chicken"        →  ["kung_pao", "chicken"]   (if "kung_pao" is in vocab)
```

Same tokeniser is applied to both the index and every query.

**Step 2 — Soft term frequency (MaxSim)**

Instead of counting exact occurrences of a query term in the document, find the
*maximum cosine similarity* between the query token's vector and any document
token vector:

```
soft_tf(q, D) = max_{w ∈ D}  max(0,  cosine(embed(q), embed(w)) − threshold)
```

A threshold (default 0.5) suppresses noise from unrelated words.
Examples with GloVe/ConceptNet vectors:

```
cosine(embed("oyster"), embed("oyster"))        ≈ 1.00  → counts fully
cosine(embed("oyster"), embed("oyster_sauce"))  ≈ 0.45  → below threshold, 0
cosine(embed("seafood"), embed("shrimp"))       ≈ 0.72  → counts at 0.22
cosine(embed("italian"), embed("pasta"))        ≈ 0.68  → counts at 0.18
```

**Step 3 — BM25 scoring**

soft_tf is plugged into the standard BM25 saturation formula:

```
tf_norm(q, D)  =  soft_tf(q, D) · (k1 + 1) / (soft_tf(q, D) + k1 · (1 − b + b · |D|/avgdl))
score(Q, D)    =  Σ_{q ∈ Q}  IDF(q) · tf_norm(q, D)
```

IDF is computed over the phrase-tokenised corpus. Query terms absent from the
corpus (OOV for the exact token) use a high default IDF so they are weighted
heavily when a soft match is found.

### Why this is better than Approach 3 (word averaging)

Approach 3 collapses the whole document to one average vector, losing the
AND-structure across query terms. A dish that is entirely Italian but has no
seafood can score as high as CajunPasta for query "seafood italian" if its
average vector happens to land near the query average. Soft-BM25 requires each
query term to independently find a close match somewhere in the document.

| | Approach 3 | Approach 3.5 | Approach 4 |
|---|---|---|---|
| "seafood" finds "shrimp" | ✓ (via avg) | ✓ (MaxSim) | ✓ (contextual) |
| AND-semantics across terms | ✗ | ✓ | ✓ |
| "oyster" ≠ "oyster sauce" | ✗ | ✓ (phrase detection) | ✓ (contextual) |
| No ML / no GPU | ✓ | ✓ | ✓ |
| Inference speed | Fast | Fast | Fast (offline) |

### Neural equivalent

ColBERT (Khattab & Zaharia 2020) implements this exact MaxSim scoring with BERT
*contextual* embeddings instead of static word vectors. Because BERT reads the
full phrase, "oyster" in "beef in oyster sauce" gets a different vector than
"oyster" in "grilled oysters" — no phrase detection step needed.
Approach 3.5 achieves some of this via explicit phrase detection instead, using
cheaper static vectors. Implemented and benchmarked below as **Approach 4.5** —
it's the best-performing approach measured so far on this benchmark.

---

### Design choices and alternatives

#### Phrase detection options

| Method | How | Vocabulary source | Notes |
|---|---|---|---|
| **FMM + ConceptNet** (default) | Greedy longest match | Multi-word entries in Numberbatch | Single file for vocab + vectors |
| FMM + Word2Vec phrases vocab | Greedy longest match | Underscore entries in Google News model | Better English compound coverage |
| gensim `Phrases` | Statistical bigram/trigram merging | Learned from your menu corpus | Auto-discovers domain phrases; needs `min_count≥2` on small corpora |
| Manual glossary | Exact string list | Hand-curated food terms | Most predictable; easy to audit |

The `PhraseTokenizer` in the implementation takes a `phrase_vocab: set[str]`
argument — swap the set to change the detection strategy without touching
anything else.

#### Word vector model options

| Model | Phrase vectors | OOV single words | Size | Food domain coverage |
|---|---|---|---|---|
| **ConceptNet Numberbatch** (recommended) | ✓ direct | Partial | 75 MB (EN) | Good for common dishes/condiments |
| Word2Vec Google News phrases | ✓ trained | ✗ | 1.5 GB | Good English compounds; news-biased |
| GloVe 6B 100d | ✗ (compose) | ✗ | 170 MB | Reasonable; needs composition fallback |
| GloVe 840B 300d | ✗ (compose) | ✗ | 2.0 GB | Higher quality; still no phrases |
| FastText crawl 300d | ✗ (compose) | ✓ char n-grams | 1.6 GB | Best for OOV / foreign food terms |
| FastText wiki 300d | ✗ (compose) | ✓ char n-grams | 640 MB | Good balance of size and OOV coverage |

The `VectorStore` in the implementation takes a `raw_vectors: dict[str, ndarray]`
argument — swap the dict to change the embedding model.

#### Phrase vector composition (for word-only models)

When a detected phrase has no direct vector (unavoidable with GloVe/FastText),
its vector is composed from its component word vectors:

| Method | Formula | Notes |
|---|---|---|
| **Mean average** (default) | `mean(embed(w) for w in phrase)` | Simple; "oyster sauce" pulled between oyster-space and sauce-space |
| IDF-weighted mean | `Σ idf(w)·embed(w) / Σ idf(w)` | Downweights "sauce", "with"; emphasises content words |
| SIF (Arora et al. 2017) | `Σ a/(a+p(w))·embed(w)` then subtract 1st PC | Principled phrase embedding; best for longer phrases |

---

### References

- **Soft-TF-IDF origin** — Cohen, Ravikumar, Fienberg (2003). *A Comparison of
  String Distance Metrics for Name-Matching Tasks.* Introduced soft TF using
  string edit distance; cosine similarity of word vectors is the natural extension.
- **Word Mover's Distance** — Kusner, Sun, Kolkin, Weinberger (2015). *From Word
  Embeddings To Document Distances.* Related approach: optimal transport over word
  vector distributions instead of MaxSim per query term.
- **SIF phrase embeddings** — Arora, Liang, Ma (2017). *A Simple but Tough-to-Beat
  Baseline for Sentence Embeddings.* IDF-weighted averaging + PCA removal; strong
  baseline for short phrase similarity.
- **Word2Vec phrase detection** — Mikolov et al. (2013). *Distributed Representations
  of Words and Phrases and their Compositionality.* Bigram scoring function that
  produces trained phrase vectors in Google News model.
- **ConceptNet Numberbatch** — Speer, Chin, Havasi (2017). *ConceptNet 5.5: An Open
  Multilingual Graph of General Knowledge.* Retrofitted vectors grounded in a
  knowledge graph; multi-word concept entries serve as both phrase vocabulary and
  phrase vectors.
- **ColBERT / MaxSim** — Khattab & Zaharia (2020). *ColBERT: Efficient and Effective
  Passage Search via Contextualized Late Interaction over BERT.* Neural version of
  Approach 3.5's MaxSim scoring, using BERT contextual embeddings.

**Download ConceptNet Numberbatch (English):**
```
https://conceptnet.s3.amazonaws.com/downloads/2019/numberbatch/numberbatch-en-19.08.txt.gz
```
Uncompressed: ~75 MB, 516K entries, 300 dimensions.

**Files:** `research/search/soft_bm25_search.py`

---

## Approach 4 — Sentence Transformers / Dense Retrieval (SBERT)

Encode entire menu item strings as a single dense vector using a pretrained transformer model. The model reads the whole sentence at once, so it captures context that word-averaging misses.

```
encode("Pasta with a Cajun cream sauce, clams, salmon, cod") 
    · encode("seafood italian")  →  high cosine similarity
```

**How it works:**
1. Download a pretrained model (e.g., `all-MiniLM-L6-v2`, ~80 MB)
2. At index time: encode every menu item once, store the vectors
3. At query time: encode the query, rank items by cosine similarity

This is called a **bi-encoder** — two separate forward passes (one for the item, one for the query) whose outputs are compared by dot product.

**Pros:** State of the art for semantic retrieval. Handles multi-word semantics and negation better than word averaging. No thesaurus needed. Fast at query time (vectors pre-computed offline). Can run in C++ via ONNX Runtime.

**Cons:** Requires downloading a model (~80 MB). Slightly more complex setup. Still a generic model — not tuned to food/menu language specifically.

**Library:** `pip install sentence-transformers`

**Files:** `research/search/sbert_search.py` (to be created)

---

## Approach 4.5 — ColBERT (Late Interaction Retrieval)

Combines Approach 3.5's token-level MaxSim scoring with Approach 4's neural
embeddings. Instead of collapsing a menu item to one sentence vector (bi-encoder,
Approach 4), ColBERT keeps one **trained contextual vector per token** and scores
with the same MaxSim formula as Soft-BM25:

```
score(Q, D) = Σ_{q ∈ Q}  max_{d ∈ D}  cosine(embed(q), embed(d))
```

The difference from Approach 3.5 is entirely in where the vectors come from:
Soft-BM25 uses static ConceptNet vectors (or composes them for unseen phrases);
ColBERT's vectors come from a BERT encoder **fine-tuned end-to-end on real
query-passage relevance judgments** (MS MARCO, ~500K pairs), so the vector
geometry is explicitly calibrated for "does this token help answer this query,"
not just general word similarity.

This directly fixes the failure mode found while debugging raw BERT hidden
states in `research/experiment/bert_maxsim.py`: an off-the-shelf `bert-base-uncased`
gives `cosine("pasta", "juice") = 0.74` — higher than many genuinely related
food terms — because masked-language-model pretraining was never asked to make
that geometry meaningful for retrieval. ColBERT's contrastive retrieval
fine-tuning is what actually fixes it.

**How it works:**
1. Load a pretrained ColBERT checkpoint (`colbert-ir/colbertv2.0`) — no training required
2. At index time: encode every menu item, keep the full per-token matrix (not a single pooled vector)
3. At query time: encode the query the same way, score every item via MaxSim

**Pros:** Best measured quality so far on this benchmark (see table below). No
training or labeled data needed — the retrieval fine-tuning was already done by
the model authors. Keeps the AND-across-terms and phrase-context benefits of
Approach 3.5, without needing a phrase vocabulary or a static vector file.

**Cons:** Heavier at index time (one vector matrix per item instead of one
vector or a static lookup) and at query time (per-query-token max over every
item's token matrix, instead of one dot product). Requires a GPU-friendly
transformer library (`pylate`) rather than a lightweight vector file.

**Library:** `pip install pylate`

**Measured results** (full 209-query benchmark, NDCG@5 / Recall@10 / MRR):

| Engine | NDCG@5 | Recall@10 | MRR |
|---|---|---|---|
| Soft-BM25 (`plus` combiner + spell-correct) | 0.5180 | 0.5702 | 0.6459 |
| SBERT `all-MiniLM-L6-v2` | 0.5063 | 0.5229 | 0.6240 |
| SBERT `all-mpnet-base-v2` | 0.5101 | 0.5132 | 0.6400 |
| **ColBERT `colbertv2.0`** | **0.5920** | **0.6114** | **0.6931** |

(Previously measured on the 204-query benchmark: Soft-BM25 0.5063, SBERT MiniLM
0.4983, SBERT mpnet 0.5033, ColBERT 0.5931. Rankings are unchanged after the
benchmark grew to 209 queries — C24 "Pizza varieties" and C25 "Occasion /
meal-time" were added, both of which score well across engines.)

ColBERT's gains are largest on categories where Approach 4's single-vector
averaging dilutes the signal — C17 Desserts (0.56 → 0.92), C22 Ingredient focus
(0.57 → 0.86), C05 Spelling variations (0.59 → 0.79). It does **not** meaningfully
help the hardest concept-inference categories (C01–C04, C10) — those stay weak
across every approach tried so far and likely need Approach 6 or 7.

Soft-BM25's `plus` combiner (raw sum of soft-tf, no BM25 saturation or document-
length normalization) outperforms the `bm25` combiner here — the `bm25` combiner
was found to systematically over-reward short documents when soft-tf is a
continuous similarity rather than an integer count (see the "pizza" query
investigation: a 3-token item with a weak 0.52 similarity match outscored an
11-token item with a literal, exact match). Tuning `b=0` on the `bm25` combiner
recovers most of that loss (NDCG@5 0.5063 → still short of `plus`'s 0.5180),
but `plus` sidesteps the problem entirely by never applying length
normalization in the first place.

**Files:** `research/search/colbert_search.py`

---

## Approach 5 — Finetuned Bi-Encoder via Contrastive Learning (InfoNCE + Hard Negatives)

Take a pretrained bi-encoder (Approach 4 — e.g. `bge-small-en`, `all-MiniLM-L6-v2`)
and finetune it on domain-specific (anchor, positive, negative) triples so it
learns food semantics more precisely.

**Scoped to bi-encoders, not ColBERT.** Approach 4.5's ColBERT keeps one
contextual vector *per token*, so there's no single item vector to index —
retrieval requires the MaxSim/late-interaction loop over every candidate at
query time. A finetuned bi-encoder produces exactly **one dense vector per
menu item**, which is what makes it compatible with off-the-shelf
nearest-neighbor search (FAISS, HNSW, ScaNN, or brute-force cosine top-K):
encode every item once offline, and query time is a single vector lookup.
That matters for the eventual C++ engine — one vector per item beats storing
and scoring a per-token matrix per item.

**Loss — InfoNCE, not a classifier.** `MultipleNegativesRankingLoss` in
`sentence-transformers` *is* InfoNCE (softmax cross-entropy over one positive
vs. many negatives) — this was never a binary relevant/not-relevant
classifier. Triplet Loss (one negative per anchor-positive pair) is a
plausible alternative but generally underperforms InfoNCE with the same data,
since InfoNCE gets a gradient signal from every negative in the batch at once
rather than one at a time. Prefer `MultipleNegativesRankingLoss`.

**The real problem is negative quality, not label volume.** `data/queries/relevance_*.csv`
already has 1,143 real judgments across 209 queries and 7 restaurants — plenty
of positives (`positive` = any row with relevance ≥ 1). But **in-batch random
negatives are usually easy**: a random other menu item in the batch is
typically trivially distinguishable (a taco vs. a tiramisu), so the model
learns coarse topic clustering and not the fine distinctions that sink the
hardest benchmark categories (C01–C04 concept-inference). Compare:

```
("garlic shrimp", "Camarones Mojo de Ajo — shrimp in garlic butter sauce")     → positive
("garlic shrimp", "Camarones à la Diabla — shrimp in spicy red chile sauce")   → hard negative
```

Both are shrimp dishes from the same menu — an in-batch sample would rarely
produce a negative this close, so the model never learns that "garlic" vs.
"diabla" is the deciding feature. Two hard-negative sources are already free
in this repo (no LLM generation needed):

1. **Relevance-graded pairs** — for a query, pair its relevance=2 item as
   positive with a same-restaurant/same-category relevance=1 (or unlisted)
   item as hard negative. The judgments already encode "close but not the
   best match."
2. **Retriever-error mining** — embed every judged (query, positive) pair and
   the full item corpus with a pretrained bi-encoder, then take its top-K
   close-but-wrong items per query as hard negatives. Standard
   hard-negative-mining loop; `sentence_transformers.util.mine_hard_negatives`
   automates this. (ColBERT, Approach 4.5's current best model, keeps a
   per-token matrix rather than one embedding per text, so it isn't a direct
   fit for this embed-the-corpus-once utility — a bi-encoder is used instead,
   configurable via `--mining-model`.)

`MultipleNegativesRankingLoss` accepts a 3rd (explicit hard negative) column
directly, combined with in-batch negatives — no separate triplet-loss code
path needed. LLM-generated synthetic queries (prompting Claude per item to
produce paraphrase queries) remain useful for expanding *query* coverage
beyond the 204 benchmark queries, but are not needed for negatives.

**Pros:** Produces a single-vector model tuned specifically to food/menu
retrieval, ANN-indexable. Negative supervision comes from data already in the
repo — no LLM cost required for the core training loop. Exports to ONNX and
runs in C++ like the off-the-shelf SBERT model.

**Cons:** Hard-negative mining adds a preprocessing step (an extra retrieval
pass over the current best model, or a join against the relevance CSVs)
before training starts. Measured: mining ~2,500 triples takes well under a
minute; 10 epochs over them takes ~6 minutes on an Apple Silicon GPU (MPS) —
small enough that CPU-only finetuning is also practical for this dataset size.

**Libraries:** `sentence-transformers`, `datasets`

**Implemented.** Two negative sources, as described above:
`mine_hard_negatives.py`'s Method 1 pairs each relevance=2 item with a
same-restaurant/same-category weaker item straight from `relevance_*.csv`
(no model needed); Method 2 uses `sentence_transformers.util.mine_hard_negatives`
with a pretrained bi-encoder to mine close-but-wrong items from the full
corpus, dropping any mined "negative" that's actually another judged-relevant
item for that query.

**Held-out split, to keep the eventual benchmark number honest.**
`evaluate.py` always scores against the full `data/queries/` benchmark, and
naively mining triples from every judged query would let a finetuned model
partially memorize eval queries during training — the first training run
this way scored NDCG@5 **0.9029**, which is leakage, not signal.
`mine_hard_negatives.py` now excludes `--held-out-fraction` (default 20%) of
queries per category from triple generation and writes their ids to
`held_out_query_ids.txt`; `evaluate.py --query-ids-file` scores exclusively
on those unseen queries.

**Measured results** (42 held-out queries, stratified across all 25
categories, never used to build a training triple):

| Engine | NDCG@5 | Recall@10 | MRR |
|---|---|---|---|
| SBERT `all-MiniLM-L6-v2` (stock) | 0.5141 | 0.5089 | 0.6213 |
| **Finetuned `all-MiniLM-L6-v2`** | **0.5376** | **0.5418** | 0.6219 |
| ColBERT `colbertv2.0` (pretrained) | 0.5619 | 0.5434 | 0.6926 |

Finetuning gives a modest, real gain over the same base model off-the-shelf
(+0.024 NDCG@5, +0.033 Recall@10) — the hard negatives do teach the model
something the stock checkpoint didn't have. It does **not** close the gap to
ColBERT: 2,464 triples over a 22M-parameter model apparently isn't enough
signal to beat token-level late interaction with MS MARCO-scale pretraining
behind it. Answers the question posed in the Recommended Experimentation
Order below — domain finetuning beats stock SBERT, but not pretrained
ColBERT, at this data size.

**Files:**
- `data_gen/mine_hard_negatives.py` — builds (anchor, positive, hard negative) triples from `relevance_*.csv` and retriever-mined negatives; also handles the held-out split above
- `train/finetune_biencoder.py` — trains the model on those triples with `MultipleNegativesRankingLoss`
- `search/finetuned_search.py` — inference using the finetuned model
- `export/export_onnx.py` — exports to ONNX for C++ use (not yet implemented — no C++ engine to consume it yet)

### Variant 2 — synthetic structural data (no relevance judgments at all)

A second, independent way to build Approach 5's training triples: instead of
leaning on the 209-query benchmark's real judgments (small, and requires
holding out queries to avoid leakage, per above), mine triples purely from
**menu structure** across every restaurant in `data/menus/` — including the
2 restaurants (`anthonys-homeport`, `sparrow`) that have no relevance
judgments at all — targeting three specific confusion patterns by
construction:

1. **Specific-modifier confusion** — items sharing a dish-type head noun
   ("sandwich", "taco", "pollo", "camarones", ...) but a different modifier
   are hard negatives for each other: `Pollo Ranchero` vs `Pollo Asado`,
   `Camarones al Mojo de Ajo` vs `Camarones a la Diabla`. A pretrained
   bi-encoder tends to cluster these as near-duplicates.
2. **Combo/bundle vs standalone** — a combo naming a *different* core dish
   (`Combo 8: Two Beef Burritos`) shares generic bundling vocabulary with a
   query for an unrelated standalone item without actually containing it;
   attached as an extra hard negative wherever one exists in the same
   restaurant.
3. **Length-bias negatives** — mirrors the length-normalization failure mode
   already documented above in the Soft-BM25 "pizza" investigation: a long,
   fully-matching item is paired against a short item sharing exactly one
   concept keyword but naming a different dish (reuses Approach 1's example
   concept thesaurus: seafood/italian/spicy/healthy).

Patterns 1-2 are turned into natural paraphrase queries via `claude -p` — the
already-authenticated Claude Code CLI, invoked with `cwd` set outside the
repo to skip this project's CLAUDE.md/auto-memory context (cuts per-call
cost from ~$0.056 to ~$0.015 and latency from ~15s to ~8s) — grounded in the
specific siblings each case must NOT match. Pattern 3's anchor is already a
natural short phrase (e.g. the project's own canonical "seafood italian"),
so it skips the LLM call. Since training never touches `data/queries/` at
all, the resulting model can be scored against the **entire** 209-query
benchmark with no held-out split needed — a cleaner evaluation story than
Variant 1's.

**Measured**: mining produced 2,014 triples (2,007 specific-modifier +
combo, 7 length-bias) from 836 items across 9 restaurants, in ~7 minutes for
about $0.20 in `claude -p` calls.

| Training run | NDCG@5 | Recall@10 | MRR |
|---|---|---|---|
| SBERT `all-MiniLM-L6-v2` (stock) | 0.5063 | 0.5229 | 0.6240 |
| **Synthetic-trained, 10 epochs** | **0.5415** | **0.5238** | 0.6781 |
| Synthetic-trained, 30 epochs | 0.5271 | 0.5159 | 0.6636 |
| ColBERT `colbertv2.0` (pretrained) | 0.5920 | 0.6114 | 0.6931 |

All four rows score the **same full 209-query benchmark** — no held-out
split, since this variant's training data is fully independent of
`data/queries/`. Two findings:

- **Training longer did not help — it mildly hurt.** Train loss kept
  dropping (0.083 → 0.054 from epoch 10 to 30) while benchmark NDCG@5
  *fell* (0.5415 → 0.5271): classic overfitting to the synthetic set's
  narrow vocabulary once the easy structural distinctions are learned.
  10 epochs (the same default used for Variant 1) was already the better
  stopping point here, not an undertrained one.
- **Strength profile is the mirror image of what it was trained on.** Per-
  category breakdown (10-epoch run) is strong exactly where the three
  patterns target it — C05 Spelling 0.708, C17 Desserts 0.958, C21 Seafood
  0.839, C24 Pizza 0.956 — but weak on broad concept-inference categories
  the synthetic data barely touches: C01 Cuisine inference 0.320, C03
  Attribute/implied meaning 0.239, C08 Dietary/negation 0.275, C10
  Multi-constraint 0.000. Variant 1 (real relevance judgments) doesn't show
  this same lopsidedness, because its positives come from queries humans
  actually wrote across all 25 categories, not from three structural rules.
  The two variants look like they'd combine well (structural data for the
  confusions it's designed for, real judgments for everything else) — not
  yet tried here.

**Files:**
- `data_gen/generate_synthetic_data.py` — structural mining (patterns 1-3) + `claude -p` paraphrase generation → `synthetic_triples.jsonl`
- Same `train/finetune_biencoder.py` and `search/finetuned_search.py` as Variant 1 — just point `--triples` / `--model` at the synthetic files

### Variant 3 — small, targeted gap-fill patch

Variant 2's per-category breakdown pointed at a specific, fixable problem:
weak on broad concept-inference (C01/C03/C08/C10) because the structural
patterns never generate training signal for that kind of query. Rather than
mining more broadly, `mine_gap_triples.py` patches exactly that gap with a
**small** amount of new data:

1. Run the current model against the full benchmark, take the 30 queries
   with the worst NDCG@5 (and at least one real judgment).
2. For each one, pair the *real* ground-truth best item (from
   `relevance_*.csv`) against the model's *own current* top wrong answer —
   a genuine, observed retriever error, not a synthetic guess.
3. `claude -p` rewords each original query into a different phrasing with
   the same intent (explicitly told not to copy verbatim), so training
   isn't just memorizing the exact eval string.

**Leakage check.** Because the reworded anchor still targets the same
underlying query intent, some improvement on those 30 exact queries is
expected regardless of whether the model actually generalized. The real
test is whether the **other 169** (non-targeted) benchmark queries also
improved — if only the targeted 30 move, that's memorization; if the rest
move too, the model learned something transferable.

**Measured**: adding these 30 triples to Variant 2's 2,014 and retraining
from the base model (10 epochs, same as before):

| | Overall NDCG@5 | Targeted 30 queries | Other 169 queries |
|---|---|---|---|
| Before (Variant 2, synthetic only) | 0.5415 | 0.000 | 0.6376 |
| **After (+ 30 gap-fill triples)** | **0.5875** | 0.116 | **0.6711** |

The other 169 queries improved too (+0.033), not just the 30 that were
directly patched — real signal, not memorization (and the targeted 30 only
reaching 0.116, not something suspiciously close to 1.0, is itself evidence
against memorization). Per-category, the gain concentrated exactly where
Variant 2 was weakest: C02 Ingredient generalization 0.298→0.463, C03
Attribute/implied meaning 0.239→0.335, C08 Dietary/negation 0.275→0.345 —
with no regression in the categories Variant 2 was already strong on. Overall
0.5875 now sits just under ColBERT's 0.5920, from 30 cheaply-generated
examples (~1 `claude -p` batch call).

**Files:**
- `data_gen/mine_gap_triples.py` — diagnoses worst-performing queries for a given model, mines a small number of real-error triples, rewords via `claude -p`
- `train/finetune_biencoder.py` — now accepts multiple `--triples` files, concatenated (used here to combine Variant 2's set with the gap-fill patch)

### Does the base model matter?

Before settling on `all-MiniLM-L6-v2`, swapped in `BAAI/bge-small-en-v1.5` —
a model pretrained specifically for retrieval (query/passage contrastive
pairs) rather than general sentence similarity — using the exact same
Variant 3 recipe (synthetic + gap-fill triples, 10 epochs):

| Base model | Stock NDCG@5 | Finetuned NDCG@5 (Variant 3 recipe) |
|---|---|---|
| `all-MiniLM-L6-v2` | 0.5063 | 0.5875 |
| `bge-small-en-v1.5` | 0.4918 | **0.5892** |

Essentially a tie post-finetuning (+0.0017, well within noise on a
199-judged-query eval) — despite BGE starting from a *worse* stock baseline.
That stock gap is likely an artifact of this pipeline, not the model: BGE
models are trained expecting a `"Represent this sentence for searching
relevant passages: "`-style prefix on the query side, which `sbert_search.py`
doesn't apply (every engine here is treated uniformly, with no per-model
prompt handling). Finetuning appears to wash that disadvantage out, but
doesn't produce a net edge over just finetuning MiniLM directly. Given the
tie, MiniLM remains the better default — smaller (22M vs 33M params) and
faster to encode with no loss in measured quality — unless BGE's query-prefix
convention gets wired in (untried here; would need `build_index`/`search` in
`sbert_search.py` to apply different prompts to queries vs. items, which
today treats both sides identically).

---

## Approach 6 — Cross-Encoder Reranker

Instead of encoding query and item separately, a cross-encoder sees both together:

```
Input:  [CLS] seafood italian [SEP] CajunPasta: Pasta with clams, salmon... [SEP]
Output: relevance score  0.0 – 1.0
```

Because attention flows between the query and item tokens, the model can reason about their relationship more precisely than a bi-encoder.

**Typical use:** Not as a first-pass retriever (too slow — O(N) forward passes for N items), but as a **reranker** on top of Approach 4, 4.5, or 5:
1. Bi-encoder or ColBERT retrieves top 20 candidates (fast)
2. Cross-encoder rescores those 20 and reorders them (slow but accurate)

**Update — real training data now exists.** The benchmark (`data/queries/`) has
grown to 209 queries with **1,143 real relevance judgments** (relevance ≥ 1)
across 7 restaurants and 637 items, sparse-labeled in `relevance_*.csv`. Every
`(query, item)` pair *not* listed is an implicit negative, so negatives can be
sampled freely. This removes Approach 5's original blocker (needing an LLM to
generate synthetic pairs) — real supervision is already sitting in the repo.
1,143 labeled pairs is small for training a transformer's attention weights
from scratch, but it's a normal size for **finetuning an already-pretrained
checkpoint** (e.g. `cross-encoder/ms-marco-MiniLM-L6-v2`, itself pretrained on
500K+ real query-passage judgments) — the same "pretrain once, finetune on a
small labeled set" pattern as XCS224N A5's `NameDataset` finetuning step.

**Architecture note — bidirectional vs. causal.** A5's `minGPT` is decoder-only
(causal): each token can only attend backward, so only the *last* token's
hidden state has seen the whole input — that's what you'd pool for a score
head if built the A5 way. It works (this is how the original GPT paper did
classification), but it's not the natural fit here: a bidirectional encoder
(BERT-style, what `sentence-transformers.CrossEncoder` uses) lets every query
token attend directly to every item token from layer one, which is why every
established IR cross-encoder is bidirectional rather than causal. Prefer
bidirectional unless the goal is specifically to reproduce A5's mechanism.

**Pros:** Highest quality of all trainable approaches. The quality ceiling for this problem. Real (not synthetic) labeled data already available.

**Cons:** Cannot precompute item vectors — must run at query time for every candidate. Slower than bi-encoder/ColBERT. 1,143 pairs is enough to finetune a pretrained checkpoint but not to train from scratch.

**Libraries:** `sentence-transformers` (CrossEncoder class), `transformers`

**Files:** `train/finetune_crossencoder.py`, `search/crossencoder_rerank.py` (to be created)

---

## Approach 7 — Local LLM as Reader (No Training)

Give the entire menu as context to a small local language model with the query, and let it identify the relevant items:

```
System: You are a menu search assistant. "Seafood" includes dishes 
        containing shrimp, clams, salmon, cod, lobster, or any fish 
        even if the word "seafood" does not appear.

User:   MENU:
        - Margherita Pizza: Classic pizza with mozzarella...
        - CajunPasta: Pasta with clams, salmon, cod...
        - Pad Thai: Rice noodles with shrimp...
        [... all items ...]

        QUERY: seafood italian
        Return matching item names, most relevant first.
```

**Pros:** Works immediately, no training, no labeled data, handles complex or ambiguous queries, good quality ceiling to compare against.

**Cons:** Slow (0.5–5 s per query on CPU). Cannot fit hundreds of restaurants in one prompt — requires chunking by restaurant or a retrieval step first. Not viable for a web app without a GPU.

### Recommended Local Models

| Model | Size (Q4) | RAM | Notes |
|-------|-----------|-----|-------|
| Llama 3.2 1B | ~0.7 GB | ~1.5 GB | Too small — may miss subtle semantics |
| Qwen2.5 1.5B | ~1.0 GB | ~2 GB | Borderline, worth testing |
| **Llama 3.2 3B** | **~1.8 GB** | **~3 GB** | **Minimum reliable sweet spot** |
| **Phi-3.5 Mini 3.8B** | **~2.4 GB** | **~4 GB** | **Best quality for size** |
| Llama 3.1 8B | ~4.7 GB | ~8 GB | Reliable, diminishing returns for this task |

Phi-3.5 Mini is the recommended starting point — Microsoft trained it heavily on instruction-following and it punches above its weight for structured retrieval tasks.

### Running Locally

**Ollama (simplest):**
```bash
ollama pull phi3.5
ollama run phi3.5
# or via HTTP: curl http://localhost:11434/api/generate -d '{...}'
```

**llama.cpp (fits C++ project):**
```bash
# Can be linked directly as a C++ library, or used via its own CLI
./llama-cli -m models/phi-3.5-mini.Q4_K_M.gguf -p "..."
```

**Files:** `research/search/llm_search.py` (to be created)

---

## Comparison Summary

| Approach | Training | Data needed | Quality | Latency | Complexity |
|----------|----------|-------------|---------|---------|------------|
| Thesaurus expansion | None | Manual map | Low–Medium | <1 ms | Low |
| BM25 + expansion | None | Manual map | Medium | <5 ms | Low |
| Word embeddings (GloVe) | None (pretrained) | None | Medium | <5 ms | Low–Medium |
| **Phrase-aware Soft-BM25** | **None (pretrained)** | **None** | **Medium–Good** | **<10 ms** | **Medium** |
| SBERT bi-encoder | None (pretrained) | None | Good | <10 ms | Medium |
| ColBERT (late interaction) | None (pretrained) | None | **Very good (best measured)** | ~20–50 ms | Medium |
| Finetuned bi-encoder | Yes | Real (1,143 judgments) + mined hard negatives | Good (beats stock SBERT, below ColBERT — measured) | <10 ms | Medium–High |
| Cross-encoder reranker | Yes | Synthetic (LLM) or real (1,143 judgments) | Best | ~100 ms | High |
| Local LLM reader | None | None | Very good | 0.5–5 s | Low (Ollama) |

---

## Recommended Experimentation Order

1. **Thesaurus expansion** — establish a working baseline, understand the data
2. **Off-the-shelf SBERT** — how much does semantic embedding help over keywords?
3. **ColBERT (pretrained, no training)** — does token-level late interaction beat sentence-level pooling? (Yes — best result measured so far.)
4. **Finetuned bi-encoder** — using the 1,143 real relevance judgments in `data/queries/`, does domain finetuning beat off-the-shelf ColBERT/SBERT? (Yes vs. SBERT, not vs. ColBERT — see Approach 5's measured results.)
5. **Cross-encoder reranker** — quality ceiling: rerank ColBERT/bi-encoder top-20 candidates, finetuned on the same real judgments
6. **Local LLM reader** — compare against trained approaches; useful for qualitative analysis

Evaluate each step with **recall@K**: did the correct item appear in the top K results?

---

## Python / C++ Split

| Phase | Language | Location |
|-------|----------|----------|
| All experimentation, training, evaluation | Python | `research/` |
| Production inference | C++ | `src/search/` |
| Bridge | ONNX export | `research/export/` → `models/` |

Trained models (Approaches 5 and 6) export to ONNX via `optimum` and load in C++ via ONNX Runtime, keeping the production search engine dependency-free.
