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

## Approach 5 — Finetuned Bi-Encoder with Synthetic Training Data

Take a pretrained bi-encoder (Approach 4) and finetune it on domain-specific (query, menu item) pairs so it learns food semantics more precisely.

**The labeled data problem:** You need pairs like:
```
("seafood pasta",  "CajunPasta with clams, salmon, cod")  → relevant
("seafood pasta",  "Tiramisu with espresso")               → not relevant
```
This is expensive to collect manually.

**Solution — synthetic data generation via LLM:**
1. For each menu item, prompt Claude to generate 5–10 queries that should match it
2. Example: "CajunPasta with clams, salmon, cod" → Claude generates:
   - `"seafood pasta"`, `"Italian dish with fish"`, `"pasta with shellfish"`, `"cajun seafood"`, ...
3. Treat other items in the same batch as negatives (in-batch negative sampling)
4. Finetune `all-MiniLM-L6-v2` on these pairs using `MultipleNegativesRankingLoss`

**Pros:** Produces a model tuned specifically to food/menu retrieval. No manual labeling. The finetuned model exports to ONNX and runs in C++ just like the off-the-shelf SBERT model.

**Cons:** Requires running Claude API for synthetic data generation (~small cost). Requires a GPU or patience for finetuning (small model, ~30 min on CPU for this dataset size).

**Libraries:** `sentence-transformers`, `anthropic`, `datasets`

**Files:**
- `data_gen/generate_pairs.py` — calls Claude to generate (query, item) pairs
- `train/finetune_biencoder.py` — trains the model on those pairs
- `export/export_onnx.py` — exports to ONNX for C++ use
- `search/finetuned_search.py` — inference using the finetuned model

---

## Approach 6 — Cross-Encoder Reranker

Instead of encoding query and item separately, a cross-encoder sees both together:

```
Input:  [CLS] seafood italian [SEP] CajunPasta: Pasta with clams, salmon... [SEP]
Output: relevance score  0.0 – 1.0
```

Because attention flows between the query and item tokens, the model can reason about their relationship more precisely than a bi-encoder.

**Typical use:** Not as a first-pass retriever (too slow — O(N) forward passes for N items), but as a **reranker** on top of Approach 4 or 5:
1. Bi-encoder retrieves top 20 candidates (fast)
2. Cross-encoder rescores those 20 and reorders them (slow but accurate)

**Pros:** Highest quality of all trainable approaches. The quality ceiling for this problem.

**Cons:** Cannot precompute item vectors — must run at query time for every candidate. Slower than bi-encoder. Still needs labeled or synthetic training data.

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
| SBERT bi-encoder | None (pretrained) | None | Good | <10 ms | Medium |
| Finetuned bi-encoder | Yes | Synthetic (LLM) | Very good | <10 ms | Medium–High |
| Cross-encoder reranker | Yes | Synthetic (LLM) | Best | ~100 ms | High |
| Local LLM reader | None | None | Very good | 0.5–5 s | Low (Ollama) |

---

## Recommended Experimentation Order

1. **Thesaurus expansion** — establish a working baseline, understand the data
2. **Off-the-shelf SBERT** — how much does semantic embedding help over keywords?
3. **Synthetic data generation** — use Claude to create (query → item) training pairs
4. **Finetuned bi-encoder** — does domain adaptation improve over generic SBERT?
5. **Cross-encoder reranker** — quality ceiling: rerank bi-encoder top-20 candidates
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
