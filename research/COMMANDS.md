# Command Reference

Example command lines for running the search experiments in `research/`. Kept
up to date as scripts gain flags — check `--help` for the authoritative list.

All commands assume the `search` conda environment and are run from the repo
root:

```bash
conda activate search
```

---

## Environment setup (new machine)

```bash
conda create -n search python=3.11
conda activate search
pip install -r research/requirements.txt

# spacy's small English model — used by the spacy_bert segmenter option in
# evaluate.py; not installable via requirements.txt since it's not a
# regular PyPI package
python -m spacy download en_core_web_sm
```

`research/requirements.txt` only lists what `research/search/*.py` actually
imports today (faiss, Flask, numpy, pylate, pyspellchecker,
sentence-transformers, spacy, torch, transformers). It has commented-out
sections for packages needed by future approaches (BM25, finetuning, ONNX
export, local LLM) — uncomment as those get implemented.

Verify the install:

```bash
python research/search/text_search.py seafood
python research/search/evaluate.py --engine sbert --model all-MiniLM-L6-v2
```

---

## Downloading the vectors for `--engine soft_bm25`

`soft_bm25` needs a local ConceptNet Numberbatch vectors file passed via
`--vectors`. It is not checked into the repo (~75 MB uncompressed).

```bash
mkdir -p models
curl -L -o models/numberbatch-en.txt.gz \
    https://conceptnet.s3.amazonaws.com/downloads/2019/numberbatch/numberbatch-en-19.08.txt.gz
gunzip models/numberbatch-en.txt.gz
```

Result: `models/numberbatch-en.txt` (516K entries, 300 dimensions) — this is
the path used throughout the `--engine soft_bm25` examples below and in
`research/APPROACHES.md`.

---

## `text_search.py` — baseline substring search

No flags; positional query words, searches `data/menus/` directly.

```bash
python research/search/text_search.py seafood
python research/search/text_search.py spicy pasta
```

## `doc_search.py` — grep-like concept search over arbitrary files

Same search engines as `evaluate.py`, but runs against any text/markdown
files or directories instead of the benchmark data — useful for trying a
query against a single doc (e.g. `APPROACHES.md`) or a folder of menus.

```bash
python research/search/doc_search.py --engine soft_bm25 --vectors models/numberbatch-en.txt 'encoder' research/APPROACHES.md
python research/search/doc_search.py --engine sbert 'seafood italian' data/menus/*.md
python research/search/doc_search.py --engine colbert --top 10 'spicy noodles' data/menus/
python research/search/doc_search.py --engine text 'pasta' data/menus/ --ext .md
```

## `web_search.py` — browser UI for the same engines

Same flags as `doc_search.py`, plus `--port` / `--no-browser`; serves results
in a browser tab instead of printing them.

```bash
python research/search/web_search.py --engine colbert --top 10 data/menus/*.md
python research/search/web_search.py --engine soft_bm25 --vectors models/numberbatch-en.txt --combiner plus data/menus/
python research/search/web_search.py --engine sbert --model all-mpnet-base-v2 --port 8080 myfile.md
```

## `colbert_search.py` — ColBERT late-interaction search directly

```bash
python research/search/colbert_search.py seafood pasta
python research/search/colbert_search.py --show-tokens spicy noodles
python research/search/colbert_search.py --model colbert-ir/colbertv2.0 --query-length 32 healthy vegetarian
```

## Approach 5 — finetuned bi-encoder

Three steps: mine hard-negative training triples, finetune, then search/evaluate
the result exactly like any other `sbert`-family model (a finetuned model is
still just a `SentenceTransformer`, loaded from a local directory instead of
a hub name).

```bash
# 1. Build (anchor, positive, hard_negative) triples from data/queries/relevance_*.csv
python research/data_gen/mine_hard_negatives.py
python research/data_gen/mine_hard_negatives.py --skip-retriever-mining   # fast, no model download
python research/data_gen/mine_hard_negatives.py --mining-model all-mpnet-base-v2 --num-negatives 5

# 2. Finetune (writes to models/finetuned-<base-model> by default)
python research/train/finetune_biencoder.py
python research/train/finetune_biencoder.py --base-model all-MiniLM-L6-v2 --epochs 10 --batch-size 16

# 3a. Search directly
python research/search/finetuned_search.py seafood italian
python research/search/finetuned_search.py --model models/finetuned-all-mpnet-base-v2 spicy noodles

# 3b. Or benchmark it like any sbert model (same --engine sbert path, just a local dir)
python research/search/evaluate.py --engine sbert --model models/finetuned-all-MiniLM-L6-v2
```

## Approach 5, variant 2 — synthetic structural data (no relevance judgments needed)

Mines triples purely from menu structure across every restaurant in
`data/menus/` — specific-modifier confusion ("chicken sandwich" vs "turkey
sandwich"), combo-vs-standalone, and length-bias negatives — then uses
`claude -p` (the already-logged-in Claude Code CLI, no separate API key) to
turn each case into natural paraphrase queries. Since training never touches
`data/queries/`, the resulting model can be scored against the **entire**
209-query benchmark with no held-out split needed.

```bash
# Mine structural cases + LLM paraphrase queries (~2,000 triples, ~7 min, ~$0.20 in claude -p calls)
python research/data_gen/generate_synthetic_data.py
python research/data_gen/generate_synthetic_data.py --skip-llm   # free dry run: seed queries only, check case counts

# Train on synthetic triples only
python research/train/finetune_biencoder.py --triples research/data_gen/synthetic_triples.jsonl \
    --output-dir models/finetuned-synthetic-all-MiniLM-L6-v2

# Evaluate on the full benchmark (no --query-ids-file needed — nothing leaked)
python research/search/evaluate.py --engine sbert --model models/finetuned-synthetic-all-MiniLM-L6-v2
```

## Approach 5, variant 3 — small gap-fill patch for a model's worst queries

Diagnoses whatever model you point it at, mines a small number of real-error
triples from its worst-scoring queries, and rewords them via `claude -p` so
training isn't just memorizing the eval string.

```bash
# Diagnose models/finetuned-synthetic-all-MiniLM-L6-v2's 30 worst queries and patch them
python research/data_gen/mine_gap_triples.py
python research/data_gen/mine_gap_triples.py --model models/finetuned-synthetic-all-MiniLM-L6-v2 --count 30

# Retrain combining the broad synthetic set with the small gap-fill patch
python research/train/finetune_biencoder.py \
    --triples research/data_gen/synthetic_triples.jsonl research/data_gen/gap_fill_triples.jsonl \
    --output-dir models/finetuned-synthetic-plus-gapfill

python research/search/evaluate.py --engine sbert --model models/finetuned-synthetic-plus-gapfill
```

## Approach 6 — cross-encoder (exhaustive scoring)

Scores every menu item against the query (no first-stage retriever).
Training reuses Approach 5's triples, expanded in memory into labeled
(query, item) pairs plus random negatives, so there's no separate data-gen step.
On a 4-core CPU, training takes ~3.5 min and a full benchmark run ~13.5 min.
Both use a GPU automatically when one is present.

```bash
# Stock checkpoint, no training (--model defaults to cross-encoder/ms-marco-MiniLM-L6-v2 here)
python research/search/evaluate.py --engine crossencoder

# Finetune on synthetic + gap-fill triples (default) -> models/crossencoder-synthetic-plus-gapfill
python research/train/finetune_crossencoder.py
python research/train/finetune_crossencoder.py --epochs 3 --random-negatives 5 --dump-pairs /tmp/ce_pairs.jsonl

# Control: synthetic only (no benchmark judgments at all)
python research/train/finetune_crossencoder.py --triples research/data_gen/synthetic_triples.jsonl \
    --output-dir models/crossencoder-synthetic

# Evaluate a finetuned model on the full benchmark
python research/search/evaluate.py --engine crossencoder --model models/crossencoder-synthetic-plus-gapfill

# Leakage check: score only the queries NOT used to build gap_fill_triples.jsonl
python -c "import json; print('\n'.join(sorted({json.loads(l)['gap_query_id'] for l in open('research/data_gen/gap_fill_triples.jsonl')})))" > /tmp/gap_ids.txt
python research/search/evaluate.py --engine crossencoder --model models/crossencoder-synthetic-plus-gapfill \
    --exclude-query-ids-file /tmp/gap_ids.txt

# Search directly
python research/search/crossencoder_search.py --benchmark-only seafood italian
```

## Approach 7 — local LLM as reader (runs on a Colab GPU)

One prompt per (query, restaurant): the whole menu as a numbered list, and
the LLM answers with graded `[item_number, grade]` pairs. It runs with vLLM
on a Colab GPU VM via the Colab CLI (`colab --auth adc`). The driver uploads
the code and data, runs the job detached, polls it, downloads the results to
`research/results/llm/<model>.{jsonl,metrics.json,log}` and always stops the
VM. Ungated models need no tokens. For gated models (e.g. Llama), set `HF_TOKEN`.

```bash
# Full benchmark, Qwen2.5-7B-Instruct on an L4 (defaults)
research/colab/run_llm_eval.sh

# Smoke test: first 5 queries only
LIMIT=5 research/colab/run_llm_eval.sh

# Other models / GPUs
MODEL=microsoft/Phi-3.5-mini-instruct research/colab/run_llm_eval.sh
GPU=A100 MODEL=Qwen/Qwen2.5-14B-Instruct research/colab/run_llm_eval.sh

# Replay a downloaded rankings file locally (no GPU) — e.g. to slice by category
python research/search/evaluate.py --engine llm --rankings research/results/llm/qwen2.5-7b-instruct.jsonl
python research/search/evaluate.py --engine llm --rankings research/results/llm/qwen2.5-7b-instruct.jsonl --difficulty Hard -v

# On any machine with a GPU and vLLM, without Colab
python research/search/llm_search.py --model Qwen/Qwen2.5-7B-Instruct --out runs/llm.jsonl
```

Interactive queries against a long-running server. `start` installs vLLM and
loads the model once on a Colab GPU VM (~5–8 min). Each `query` after that
takes seconds. The VM bills until you run `stop`.

```bash
research/colab/llm_server.sh start                     # MODEL=… GPU=… to override
research/colab/llm_server.sh query seafood italian
research/colab/llm_server.sh query --all-restaurants vegan tacos
research/colab/llm_server.sh sync                      # push local code/menu edits to the VM
research/colab/llm_server.sh stop

# The same client works with any OpenAI-compatible server, e.g. a local Ollama.
# Raise Ollama's context first or long menus get silently truncated.
OLLAMA_CONTEXT_LENGTH=16384 ollama serve &
python research/search/llm_search.py --server http://localhost:11434 --model qwen2.5:7b seafood italian
```

## Approach 7b — Hybrid search (LLM candidate retrieval + CrossEncoder reranking)

Combines the high candidate recall of the LLM reader with the fine-grained
scoring and ordering of a CrossEncoder. Rescores LLM candidate items, optionally
adding an LLM grade boost, and falls back to full cross-encoder search over all
menu items when the LLM returns no matches.

```bash
# Search directly
python research/search/hybrid_search.py --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl seafood italian

# Benchmark evaluation (pure cross-encoder rescoring of LLM candidates + fallback)
python research/search/evaluate.py --engine hybrid \
    --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl \
    --model cross-encoder/ms-marco-MiniLM-L6-v2

# With LLM grade boost (e.g. +2.0 logit boost per LLM grade)
python research/search/evaluate.py --engine hybrid \
    --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl \
    --model cross-encoder/ms-marco-MiniLM-L6-v2 \
    --grade-boost 2.0

# With strict grade ranking (grade 2 before grade 1, intra-grade ties broken by CrossEncoder)
python research/search/evaluate.py --engine hybrid \
    --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl \
    --model cross-encoder/ms-marco-MiniLM-L6-v2 \
    --strict-grade
```

## `evaluate.py` — benchmark scoring (NDCG@5, Recall@10, MRR)

Engine modules load lazily: only the selected `--engine`'s code and libraries
are imported, and its extra flags appear in `--help` only when the engine is
given (e.g. `--engine soft_bm25 --help`).

```bash
# baseline keyword search
python research/search/evaluate.py --engine text

# thesaurus-expanded keyword search
python research/search/evaluate.py --engine enhanced
python research/search/evaluate.py --engine filtered

# Soft-BM25 (best-measured config: plus combiner + spell-correct)
python research/search/evaluate.py --engine soft_bm25 --vectors models/numberbatch-en.txt --combiner plus --spell-correct

# SBERT bi-encoder
python research/search/evaluate.py --engine sbert --model all-MiniLM-L6-v2
python research/search/evaluate.py --engine sbert --model all-mpnet-base-v2

# ColBERT late interaction
python research/search/evaluate.py --engine colbert

# Cross-encoder (scores every item; stock checkpoint unless --model is given)
python research/search/evaluate.py --engine crossencoder

# Hybrid (LLM candidates + CrossEncoder reranker)
python research/search/evaluate.py --engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl

# Save the full report (overall, by category/difficulty, per query) as JSON.
# research/results/baselines/ holds the engines that finish in under 5 minutes on CPU
python research/search/evaluate.py --engine sbert --save-metrics research/results/baselines/sbert-all-MiniLM-L6-v2.metrics.json
python research/search/evaluate.py --engine llm --rankings research/results/llm/qwen2.5-7b-instruct.jsonl \
    --save-metrics research/results/llm/qwen2.5-7b-instruct.metrics.json

# Stratify by category / difficulty
python research/search/evaluate.py --engine colbert --category C01
python research/search/evaluate.py --engine colbert --difficulty Hard --verbose
```

---

## Vector files

`--vectors` for `soft_bm25` points at the ConceptNet Numberbatch file, kept
locally at `models/numberbatch-en.txt` (not checked in — see
`research/APPROACHES.md` for the download link).
