"""
Shared engine loading for doc_search.py (CLI) and web_search.py (browser UI).

Both tools take the same document-set / engine-selection options and need the
same "load documents, build the chosen engine's index, return a
query -> list[dict] search function" pipeline. Keeping it here means the CLI
and the web UI produce identical results and neither duplicates the engine
dispatch logic.

Alongside search_fn, load_engine() also returns highlight_fn(query, text) ->
list[(start, end)] character spans to mark as "matching this query" within a
given paragraph. For text/enhanced/sbert/colbert this is literal query-word
overlap (the only signal available -- sbert/colbert score a whole paragraph
as one vector, with no per-word attribution). soft_bm25 additionally
highlights *concept* matches: any phrase token in the paragraph whose
ConceptNet vector is close to a query token's vector, even if the words
differ entirely (e.g. "seafood" lighting up "clams", "salmon", "cod").
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.text_docs import load_documents

ENGINES = ["text", "enhanced", "sbert", "colbert", "soft_bm25"]

# Similarity floor for soft_bm25 concept highlighting -- matches search()'s own
# default similarity_threshold, so a highlighted word is exactly one that would
# actually have contributed to the match score.
_CONCEPT_HIGHLIGHT_THRESHOLD = 0.5


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not spans:
        return []
    spans = sorted(spans)
    merged = [spans[0]]
    for s, e in spans[1:]:
        ls, le = merged[-1]
        if s <= le:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    return merged


def literal_highlight(query: str, text: str) -> list[tuple[int, int]]:
    """Spans covering every case-insensitive literal occurrence of a query word in text."""
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    spans = []
    for term in terms:
        for m in re.finditer(re.escape(term), text, re.IGNORECASE):
            spans.append((m.start(), m.end()))
    return _merge_spans(spans)


def add_engine_args(parser) -> None:
    """Add the document/engine selection flags shared by doc_search.py and web_search.py."""
    parser.add_argument(
        "--ext", default=".txt,.md",
        help="Comma-separated file extensions to include when a directory is passed (default: .txt,.md)",
    )
    parser.add_argument(
        "--engine", choices=ENGINES, default="sbert",
        help="Search engine (default: sbert -- best general-purpose concept match with no extra setup)",
    )
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="sentence-transformers model (--engine sbert)")
    parser.add_argument(
        "--vectors",
        help="Path to ConceptNet Numberbatch vectors file (required for --engine soft_bm25); "
             "see soft_bm25_search.py for the download link",
    )
    parser.add_argument(
        "--combiner", choices=["bm25", "plus", "product", "min"], default="plus",
        help="Score combiner for --engine soft_bm25 (default: plus -- BM25's length "
             "normalization misbehaves on small/uneven document sets like a handful of "
             "paragraphs; 'plus' is also the best-measured config in BENCHMARK_RESULTS.md)",
    )
    parser.add_argument(
        "--spell-correct", action="store_true",
        help="Spell-correct query tokens with no embedding (--engine soft_bm25 only)",
    )


def load_engine(args):
    """
    Load documents and build the selected search engine.

    Returns (documents, paragraphs, search_fn, highlight_fn):
      search_fn(query: str) -> list[dict]
      highlight_fn(query: str, text: str) -> list[(start, end)]

    Raises ValueError on bad configuration (e.g. missing --vectors for soft_bm25)
    or if no paragraphs were found.
    """
    extensions = tuple(e.strip() for e in args.ext.split(","))
    print("Loading documents...", end=" ", flush=True)
    documents, paragraphs = load_documents(args.docs, extensions=extensions)
    n_paras = sum(len(v) for v in paragraphs.values())
    print(f"{len(documents)} document(s), {n_paras} paragraph(s)")
    if n_paras == 0:
        raise ValueError("No paragraphs found -- check --docs / --ext.")

    if args.engine == "text":
        from text_search import search
        return documents, paragraphs, (lambda query: search(query, documents, paragraphs)), literal_highlight

    if args.engine == "enhanced":
        from enhanced_text_search import search
        return documents, paragraphs, (lambda query: search(query, documents, paragraphs)), literal_highlight

    if args.engine == "sbert":
        from sbert_search import build_index, search as sbert_search_fn
        from sentence_transformers import SentenceTransformer
        print(f"Loading model '{args.model}'...", end=" ", flush=True)
        model = SentenceTransformer(args.model)
        print("done")
        print("Building index...", end=" ", flush=True)
        index = build_index(paragraphs, documents, model)
        print(f"{sum(len(v) for v in index.values())} paragraphs encoded")
        search_fn = lambda query: sbert_search_fn(query, documents, index, model)
        return documents, paragraphs, search_fn, literal_highlight

    if args.engine == "colbert":
        from colbert_search import build_index, search as colbert_search_fn
        from pylate import models as pylate_models
        print("Loading ColBERT model 'colbert-ir/colbertv2.0'...", end=" ", flush=True)
        model = pylate_models.ColBERT("colbert-ir/colbertv2.0")
        print("done")
        print("Building index...", end=" ", flush=True)
        index = build_index(paragraphs, documents, model)
        print(f"{sum(len(v) for v in index.values())} paragraphs encoded")
        search_fn = lambda query: colbert_search_fn(query, documents, index, model)
        return documents, paragraphs, search_fn, literal_highlight

    # soft_bm25
    if not args.vectors:
        raise ValueError("--vectors PATH is required for --engine soft_bm25")
    from soft_bm25_search import (
        load_conceptnet, PhraseTokenizer, VectorStore, build_index,
        resolve_query_tokens, search as soft_bm25_search_fn,
    )
    print("Loading vectors...", end=" ", flush=True)
    raw_vectors, phrase_vocab = load_conceptnet(args.vectors)
    print(f"{len(raw_vectors):,} entries")
    tokenizer = PhraseTokenizer(phrase_vocab)
    vector_store = VectorStore(raw_vectors)
    print("Building index...", end=" ", flush=True)
    index, idf, avgdl = build_index(paragraphs, tokenizer, vector_store)
    print(f"{sum(len(v) for v in index.values())} paragraphs indexed")
    corrector = None
    if args.spell_correct:
        from soft_bm25_search import SpellCorrector
        corrector = SpellCorrector()

    def _search(query):
        return soft_bm25_search_fn(
            query, documents, index, idf, tokenizer, vector_store, avgdl,
            combiner=args.combiner, spell_corrector=corrector,
        )

    def _highlight(query: str, text: str) -> list[tuple[int, int]]:
        spans = list(literal_highlight(query, text))
        _, query_vecs, _ = resolve_query_tokens(query, tokenizer, vector_store, corrector)
        query_vecs = [v for v in query_vecs if v is not None]
        if query_vecs:
            for tok in set(tokenizer.tokenize(text)):
                vec = vector_store.lookup(tok)
                if vec is None:
                    continue
                sim = max(float(vec @ qv) for qv in query_vecs)
                if sim >= _CONCEPT_HIGHLIGHT_THRESHOLD:
                    phrase = tok.replace("_", " ")
                    for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                        spans.append((m.start(), m.end()))
        return _merge_spans(spans)

    return documents, paragraphs, _search, _highlight
