"""
General-purpose "grep-like" excerpt search across plain text/markdown documents.

Takes a (possibly multi-word) search query and a set of documents, and shows
the top matching paragraphs by *concept*, not just keyword substring --
e.g. searching "car" can surface a paragraph about "vehicle" upkeep even
though the word "car" never appears in it.

This reuses the menu-search engines unchanged (research/search/text_search.py,
enhanced_text_search.py, sbert_search.py, colbert_search.py, soft_bm25_search.py)
via engine.py, which also backs web_search.py (the browser UI). research/lib/
text_docs.py loads plain files into the same (restaurants, menus)-shaped
structure lib.data.load_data() uses for menus -- each document stands in for
a "restaurant" and each paragraph for a "menu item" -- so the same
build_index()/search() functions apply directly, no matching logic is
duplicated. See BENCHMARK_RESULTS.md for how these engines compare
(colbert/sbert are the strongest general "concept" matchers, soft_bm25 wins
on hard/adversarial queries, text is a fast exact-substring baseline).

Headers are not treated specially yet -- every blank-line-separated block is
indexed as a plain body paragraph, per APPROACHES.md's incremental scope.

Usage (grep-style: options, then a single quoted query, then a document list --
shell globs expand naturally into that list):
    python doc_search.py car notes.txt
    python doc_search.py --engine sbert 'seafood italian' data/menus/*.md
    python doc_search.py --engine colbert --top 10 'budget concerns' report.md notes.txt
    python doc_search.py --engine soft_bm25 --vectors models/numberbatch-en.txt \
        --combiner plus --spell-correct 'seafood italian' data/menus/*.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from engine import add_engine_args, load_engine


def _print_results(results: list[dict], query: str, engine: str, top: int) -> None:
    print(f"\nQuery: '{query}'  [{engine}]  —  showing top {min(top, len(results))} of {len(results)} match(es)\n")
    if not results:
        print("  (no matches)")
        return
    for r in results[:top]:
        score = r.get("score")
        if isinstance(score, float):
            score_str = f"[{score:.4f}] "
        elif isinstance(score, int):
            score_str = f"[{score:>3}] "
        else:
            score_str = ""
        print(f"  {score_str}{r['restaurant']}  {r['item']}")
        print(f"  {r['description']}\n")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Grep-like concept search across plain text documents",
        usage="%(prog)s [options] query doc [doc ...]",
    )
    parser.add_argument("query", help="Search query; quote it if it has multiple words, e.g. 'seafood italian'")
    parser.add_argument(
        "docs", nargs="+",
        help="Files and/or directories to search (shell globs expand naturally, e.g. data/menus/*.md); "
             "directories are scanned recursively for --ext files",
    )
    add_engine_args(parser)
    parser.add_argument("--top", type=int, default=5, help="Number of excerpts to show (default: 5)")
    args = parser.parse_args()

    try:
        _documents, _paragraphs, search_fn, _highlight_fn = load_engine(args)
    except ValueError as e:
        parser.error(str(e))

    results = search_fn(args.query)
    _print_results(results, args.query, args.engine, args.top)


if __name__ == "__main__":
    main()
