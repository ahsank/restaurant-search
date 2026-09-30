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

## `evaluate.py` — benchmark scoring (NDCG@5, Recall@10, MRR)

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

# Stratify by category / difficulty
python research/search/evaluate.py --engine colbert --category C01
python research/search/evaluate.py --engine colbert --difficulty Hard --verbose
```

---

## Vector files

`--vectors` for `soft_bm25` points at the ConceptNet Numberbatch file, kept
locally at `models/numberbatch-en.txt` (not checked in — see
`research/APPROACHES.md` for the download link).
