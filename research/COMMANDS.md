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
