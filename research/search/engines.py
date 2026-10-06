"""
Shared engine dispatch, extracted from evaluate.py so restaurant_eval.py and
search_grouped.py can reuse every engine (and every engine-specific flag from
colbert_search.cli_args() / soft_bm25_search.cli_args()) without copy-pasting
the "given --engine X, build the index and return a search_fn" logic.

Engine modules are imported lazily: only the module for the selected --engine
is ever imported, both for its CLI flags (build_arg_parser) and for its search
code (build_search_fn). Running `--engine text` never imports colbert_search,
soft_bm25_search, sentence-transformers, pylate, torch, etc.

Usage in a CLI script:
    parser = engines.build_arg_parser("My script", parents=[...])
    parser.add_argument(...)            # script-specific flags
    args = parser.parse_args()
    search_fn = engines.build_search_fn(args, restaurants, menus)
    results = search_fn("seafood pasta")

search_fn(query) -> list[dict], each dict has at least "restaurant_id" and
"name" keys (plus whatever extra fields the underlying engine returns, e.g.
"score", "description", "price", "restaurant" display name).
"""
import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent))

ENGINE_CHOICES = ["text", "enhanced", "filtered", "soft_bm25", "sbert", "colbert", "crossencoder", "llm"]

# Engines whose module contributes extra CLI flags via its own cli_args().
_ENGINE_FLAG_MODULES = {
    "soft_bm25": "soft_bm25_search",
    "colbert": "colbert_search",
    "llm": "llm_search",
}


def cli_args() -> argparse.ArgumentParser:
    """Reusable --engine/--model flag fragment; pass via parents=[...]."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--engine", choices=ENGINE_CHOICES, default="text",
        help="Search engine: text (baseline), enhanced, filtered, soft_bm25, sbert, colbert, crossencoder, llm (replays --rankings; default: text)",
    )
    parser.add_argument(
        "--model", default="all-MiniLM-L6-v2",
        help="Model name or local directory (default: all-MiniLM-L6-v2 for sbert; colbert and crossencoder substitute their own stock checkpoint when left at this default)",
    )
    return parser


def build_arg_parser(description: str, parents: list[argparse.ArgumentParser] = ()) -> argparse.ArgumentParser:
    """
    ArgumentParser with --engine/--model plus the selected engine's own flags.

    Pre-parses sys.argv for --engine alone, then imports only that engine's
    module to pull in its cli_args() fragment. Flags of unselected engines are
    therefore not registered: `--engine colbert --help` lists ColBERT's flags,
    plain `--help` doesn't.
    """
    pre = argparse.ArgumentParser(add_help=False, parents=[cli_args()])
    known, _ = pre.parse_known_args()
    engine_parents = []
    if known.engine in _ENGINE_FLAG_MODULES:
        engine_parents.append(importlib.import_module(_ENGINE_FLAG_MODULES[known.engine]).cli_args())
    return argparse.ArgumentParser(
        description=description,
        parents=[cli_args(), *engine_parents, *parents],
        epilog="Engine-specific flags are listed when --engine is given, "
               "e.g. --engine soft_bm25 --help",
    )


def build_search_fn(args: argparse.Namespace, restaurants: dict, menus: dict) -> Callable[[str], list[dict]]:
    """
    Build search_fn(query) -> list[dict] for args.engine. Prints load/index-
    building progress to stdout. Requires args to have been parsed from a
    parser built by build_arg_parser() above, so the selected engine's own
    flags are present (--vectors is required and will raise if missing for
    soft_bm25 + fmm). Only the selected engine's module is imported.
    """
    name_to_id = {v.get("name", k): k for k, v in restaurants.items()}

    if args.engine == "llm":
        # Approach 7 runs on a GPU (Colab) and writes a rankings file; replay it here.
        if not args.rankings:
            raise SystemExit("--rankings FILE is required for --engine llm "
                             "(produce one with research/colab/run_llm_eval.sh)")
        from llm_search import replay_search_fn
        print(f"Replaying LLM rankings from {args.rankings}")
        return replay_search_fn(args.rankings)

    if args.engine in ("enhanced", "filtered"):
        from enhanced_text_search import search as _enhanced_search
        _filter = args.engine == "filtered"
        def _raw_search(query, _restaurants, _menus):
            return _enhanced_search(query, _restaurants, _menus, filter_restaurant_ctx=_filter)

    elif args.engine == "soft_bm25":
        if args.segmenter == "fmm":
            if not args.vectors:
                raise SystemExit("--vectors PATH is required for --engine soft_bm25 --segmenter fmm")
            from soft_bm25_search import (
                load_conceptnet, PhraseTokenizer, VectorStore, build_index,
                search as _sbm25_search,
            )
            print("Loading vectors...", end=" ", flush=True)
            _raw_vecs, _phrase_vocab = load_conceptnet(args.vectors)
            print(f"{len(_raw_vecs):,} entries")
            _tokenizer = PhraseTokenizer(_phrase_vocab, max_phrase_len=args.max_phrase_len)
            _vstore    = VectorStore(_raw_vecs, composition=args.composition)
            print("Building index...", end=" ", flush=True)
            _index, _idf, _avgdl = build_index(menus, _tokenizer, _vstore)
            print(f"{sum(len(v) for v in _index.values())} items indexed")

            _corrector = None
            if args.spell_correct:
                from soft_bm25_search import SpellCorrector
                _corrector = SpellCorrector()

            def _raw_search(query, _restaurants, _menus):
                return _sbm25_search(query, _restaurants, _index, _idf, _tokenizer, _vstore, _avgdl,
                                     similarity_threshold=args.threshold, k1=args.k1, b=args.b,
                                     combiner=args.combiner, spell_corrector=_corrector)
        else:
            from soft_bm25_search import (
                SpacyBertEncoder, BertSubwordEncoder,
                build_index_contextual, search_contextual as _sbm25_ctx_search,
            )
            print(f"Loading BERT encoder ({args.segmenter})...", flush=True)
            _encoder = (
                SpacyBertEncoder() if args.segmenter == "spacy_bert"
                else BertSubwordEncoder()
            )
            print("Building index...")
            _index, _idf, _avgdl = build_index_contextual(menus, _encoder)
            print(f"  {sum(len(v) for v in _index.values())} items indexed, avgdl={_avgdl:.1f}")

            def _raw_search(query, _restaurants, _menus):
                return _sbm25_ctx_search(query, _restaurants, _index, _idf, _encoder, _avgdl,
                                         similarity_threshold=args.threshold, k1=args.k1, b=args.b,
                                         combiner=args.combiner)

    elif args.engine == "sbert":
        from sbert_search import build_index as _sbert_build_index, search as _sbert_search
        from sentence_transformers import SentenceTransformer
        print(f"Loading model '{args.model}'...", end=" ", flush=True)
        _sbert_model = SentenceTransformer(args.model)
        print("done")
        print("Building index...", end=" ", flush=True)
        _sbert_index = _sbert_build_index(menus, restaurants, _sbert_model)
        print(f"{sum(len(v) for v in _sbert_index.values())} items encoded")

        def _raw_search(query, _restaurants, _menus):
            return _sbert_search(query, _restaurants, _sbert_index, _sbert_model)

    elif args.engine == "colbert":
        from colbert_search import build_index as _cb_build_index, search as _cb_search
        from pylate import models as pylate_models
        _cb_model_name = args.model if args.model != "all-MiniLM-L6-v2" else "colbert-ir/colbertv2.0"
        print(f"Loading ColBERT model '{_cb_model_name}' (query_length={args.query_length or 'model default'})...", end=" ", flush=True)
        _cb_model = pylate_models.ColBERT(_cb_model_name, query_length=args.query_length)
        print("done")
        print("Building index...", end=" ", flush=True)
        _cb_index = _cb_build_index(menus, restaurants, _cb_model)
        print(f"{sum(len(v) for v in _cb_index.values())} items encoded")

        def _raw_search(query, _restaurants, _menus):
            return _cb_search(query, _restaurants, _cb_index, _cb_model)

    elif args.engine == "crossencoder":
        from crossencoder_search import STOCK_MODEL, build_index as _ce_build_index, search as _ce_search
        from sentence_transformers.cross_encoder import CrossEncoder
        _ce_model_name = args.model if args.model != "all-MiniLM-L6-v2" else STOCK_MODEL
        print(f"Loading cross-encoder '{_ce_model_name}'...", end=" ", flush=True)
        _ce_model = CrossEncoder(_ce_model_name)
        print("done")
        _ce_index = _ce_build_index(menus, restaurants)
        print(f"{len(_ce_index)} items to score per query (exhaustive, no first-stage retriever)")

        def _raw_search(query, _restaurants, _menus):
            return _ce_search(query, _restaurants, _ce_index, _ce_model)

    else:
        from text_search import search as _raw_search

    def search(query: str) -> list[dict]:
        raw = _raw_search(query, restaurants, menus)
        out = []
        for r in raw:
            rid = name_to_id.get(r["restaurant"], r["restaurant"])
            out.append({"restaurant_id": rid, "name": r["item"], **r})
        return out

    return search
