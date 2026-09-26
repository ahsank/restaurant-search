"""
Generic plain-text document loader for doc_search.py.

Splits arbitrary text/markdown files into paragraphs and returns them in the
same (restaurants, menus)-shaped structure lib.data.load_data() produces for
restaurant menus. That means every existing search engine in research/search/
(text_search, enhanced_text_search, sbert_search, colbert_search) works on
plain documents completely unchanged: each document stands in for a
"restaurant" and each paragraph stands in for a "menu item" (name = a
paragraph label used only for display, description = the paragraph text).

Headers/structure are not treated specially for now -- every blank-line
separated block, including lines that look like headings, is indexed as a
plain body paragraph.
"""
import re
from pathlib import Path

_PARA_SPLIT = re.compile(r"\n\s*\n+")


def _split_paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in _PARA_SPLIT.split(text)]
    return [p for p in paras if p]


def _iter_files(paths: list[str], extensions: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for ext in extensions:
                files.extend(sorted(p.rglob(f"*{ext}")))
        elif p.is_file():
            files.append(p)
        else:
            raise FileNotFoundError(f"No such file or directory: {raw}")
    return files


def load_documents(
    paths: list[str],
    extensions: tuple[str, ...] = (".txt", ".md"),
) -> tuple[dict, dict]:
    """
    Parse plain text/markdown files into paragraph-level "items".

    Args:
        paths: files and/or directories. Directories are scanned recursively
            for files matching `extensions`.
        extensions: file suffixes to include when a directory is passed.

    Returns:
        (documents_by_id, paragraphs_by_document_id) -- shaped exactly like
        load_data()'s (restaurants, menus) so existing search() functions
        work unmodified.
    """
    documents: dict = {}
    paragraphs: dict = {}

    for path in _iter_files(paths, extensions):
        doc_id = str(path)
        documents[doc_id] = {"id": doc_id, "name": path.name, "path": doc_id}

        text = path.read_text(errors="ignore")
        items = []
        for i, para in enumerate(_split_paragraphs(text)):
            items.append({
                "name": f"¶{i + 1}",  # paragraph label, e.g. "¶3" (display only)
                "description": para,
                "dietary": "",
                "price": None,
                "price_raw": "",
                "category": None,
                "menu_type": None,
                "restaurant_id": doc_id,
            })
        paragraphs[doc_id] = items

    return documents, paragraphs
