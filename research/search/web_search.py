"""
Browser UI for doc_search's paragraph search engines.

Loads a set of documents and builds the selected search engine once at
startup (via engine.py -- the exact same loader doc_search.py uses, so
results are identical between the CLI and this web UI). The page shows a
document list on the left; the right pane renders the full text of whichever
document is selected, with matching paragraphs highlighted and "next
match" / "prev match" controls that jump across paragraphs -- and across
documents -- in ranked order.

Word-level highlighting is literal query-word overlap for every engine
(text, enhanced, sbert, colbert) since that's the only signal available for
whole-paragraph embedding engines. soft_bm25 additionally highlights
*concept* matches: any word/phrase in the paragraph whose ConceptNet vector
is close to a query word's vector, even when the words differ entirely
(e.g. "seafood" also lights up "clams", "salmon", "cod"). True token-level
attribution isn't implemented for sbert/colbert -- both collapse a paragraph
to one embedding, so there's no sub-paragraph score to highlight from.

Requires Flask (`pip install flask`); everything else reuses the existing
research/search/*.py engines unchanged.

Usage:
    python web_search.py data/menus/*.md
    python web_search.py --engine colbert --port 8080 report.md notes.txt
    python web_search.py --engine soft_bm25 --vectors models/numberbatch-en.txt \
        --combiner plus data/menus/*.md
"""
import sys
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

sys.path.insert(0, str(Path(__file__).parent))
from engine import add_engine_args, load_engine

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Document Search</title>
<style>
  :root {
    color-scheme: light dark;
    --fg: #1a1a1a; --bg: #ffffff; --muted: #666; --border: #e2e2e2;
    --accent: #2563eb; --card: #f8f9fa; --mark-bg: #fff29a; --mark-fg: #1a1a1a;
    --match-bg: #fffdf3; --current-ring: #2563eb;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --fg: #e8e8e8; --bg: #14161a; --muted: #9aa0a6; --border: #2a2d33; --card: #1c1f24;
      --mark-bg: #6b5b1e; --mark-fg: #fff3c4; --match-bg: #20211a; --current-ring: #5b8def;
    }
  }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0; color: var(--fg); background: var(--bg);
    display: flex; flex-direction: column; height: 100vh;
  }
  header {
    padding: 0.85rem 1.25rem; border-bottom: 1px solid var(--border);
    display: flex; flex-direction: column; gap: 0.5rem;
  }
  h1 { font-size: 1.15rem; margin: 0; }
  .subtitle { color: var(--muted); font-size: 0.8rem; }
  .search-row { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  form { display: flex; gap: 0.5rem; flex: 1; min-width: 240px; }
  input[type=text] {
    flex: 1; padding: 0.5rem 0.7rem; font-size: 0.95rem; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg); color: var(--fg);
  }
  input[type=text]:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
  button {
    padding: 0.5rem 0.9rem; font-size: 0.9rem; cursor: pointer; border-radius: 8px;
    border: 1px solid var(--accent); background: var(--accent); color: white; white-space: nowrap;
  }
  button.secondary { background: var(--bg); color: var(--fg); border-color: var(--border); }
  button:disabled { opacity: 0.5; cursor: default; }
  #status { color: var(--muted); font-size: 0.82rem; }
  .layout { flex: 1; display: flex; min-height: 0; }
  aside {
    width: 260px; flex-shrink: 0; overflow-y: auto; border-right: 1px solid var(--border);
    padding: 0.5rem;
  }
  .doc-entry {
    display: flex; justify-content: space-between; gap: 0.5rem; padding: 0.5rem 0.6rem;
    border-radius: 8px; cursor: pointer; font-size: 0.88rem; margin-bottom: 0.15rem;
  }
  .doc-entry:hover { background: var(--card); }
  .doc-entry.active { background: var(--card); font-weight: 600; }
  .doc-entry .badge {
    color: var(--muted); font-size: 0.78rem; background: var(--card);
    border-radius: 999px; padding: 0.05rem 0.5rem; min-width: 1.4em; text-align: center;
  }
  .doc-entry.has-matches .badge { color: var(--fg); background: var(--mark-bg); }
  main { flex: 1; overflow-y: auto; padding: 1.25rem 1.75rem; }
  #doc-title { font-size: 1.05rem; font-weight: 600; margin-bottom: 0.9rem; }
  .para {
    padding: 0.55rem 0.75rem; margin-bottom: 0.6rem; border-radius: 8px;
    white-space: pre-wrap; line-height: 1.5; font-size: 0.95rem;
  }
  .para.is-match { background: var(--match-bg); border: 1px solid var(--border); }
  .para.is-current { box-shadow: 0 0 0 2px var(--current-ring); }
  .para .score { float: right; color: var(--muted); font-size: 0.75rem; }
  mark { background: var(--mark-bg); color: var(--mark-fg); border-radius: 3px; padding: 0 0.1em; }
  .empty { color: var(--muted); padding: 2rem 0; text-align: center; }
</style>
</head>
<body>
  <header>
    <h1>Document Search</h1>
    <div class="subtitle">Engine: {{ engine }} &middot; {{ n_docs }} document(s), {{ n_paragraphs }} paragraph(s) indexed</div>
    <div class="search-row">
      <form id="search-form">
        <input type="text" id="q" name="q" placeholder="Search terms, e.g. seafood italian" autofocus autocomplete="off">
        <button type="submit">Search</button>
      </form>
      <button type="button" class="secondary" id="prev-match" disabled>&#9664; Prev match</button>
      <button type="button" class="secondary" id="next-match" disabled>Next match &#9654;</button>
      <span id="status"></span>
    </div>
  </header>
  <div class="layout">
    <aside id="doc-list"></aside>
    <main id="doc-view"><div class="empty">Loading documents…</div></main>
  </div>

<script>
const state = {
  documents: [],          // [{id, name, n_paragraphs}]
  docCache: {},           // id -> {id, name, paragraphs: [{index, text}]}
  currentDocId: null,
  matches: [],            // flat ranked list from the last search, each with doc_id (nullable)
  matchesByKey: {},        // "doc_id:para_index" -> match
  matchesByDoc: {},        // doc_id -> count
  pointer: -1,            // index into matches (only entries with doc_id != null count)
  query: '',
};

const form = document.getElementById('search-form');
const input = document.getElementById('q');
const status = document.getElementById('status');
const docList = document.getElementById('doc-list');
const docView = document.getElementById('doc-view');
const prevBtn = document.getElementById('prev-match');
const nextBtn = document.getElementById('next-match');

function navigableMatches() {
  return state.matches.filter(m => m.doc_id !== null && m.para_index !== null);
}

function renderSidebar() {
  docList.innerHTML = '';
  for (const doc of state.documents) {
    const count = state.matchesByDoc[doc.id] || 0;
    const entry = document.createElement('div');
    entry.className = 'doc-entry' + (doc.id === state.currentDocId ? ' active' : '') + (count > 0 ? ' has-matches' : '');
    const name = document.createElement('span');
    name.textContent = doc.name;
    entry.appendChild(name);
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = state.query ? count : doc.n_paragraphs;
    entry.appendChild(badge);
    entry.addEventListener('click', () => selectDocument(doc.id));
    docList.appendChild(entry);
  }
}

function applyHighlights(text, spans) {
  const frag = document.createDocumentFragment();
  let cursor = 0;
  for (const [s, e] of spans) {
    if (s > cursor) frag.appendChild(document.createTextNode(text.slice(cursor, s)));
    const mark = document.createElement('mark');
    mark.textContent = text.slice(s, e);
    frag.appendChild(mark);
    cursor = Math.max(cursor, e);
  }
  if (cursor < text.length) frag.appendChild(document.createTextNode(text.slice(cursor)));
  return frag;
}

function renderDocument(doc) {
  docView.innerHTML = '';
  const title = document.createElement('div');
  title.id = 'doc-title';
  title.textContent = doc.name;
  docView.appendChild(title);

  for (const para of doc.paragraphs) {
    const key = doc.id + ':' + para.index;
    const match = state.matchesByKey[key];
    const div = document.createElement('div');
    div.className = 'para' + (match ? ' is-match' : '');
    div.id = 'para-' + para.index;
    if (match && typeof match.score === 'number') {
      const score = document.createElement('span');
      score.className = 'score';
      score.textContent = 'score ' + match.score;
      div.appendChild(score);
    }
    const body = document.createElement('div');
    if (match && match.highlights && match.highlights.length) {
      body.appendChild(applyHighlights(para.text, match.highlights));
    } else {
      body.textContent = para.text;
    }
    div.appendChild(body);
    docView.appendChild(div);
  }
}

async function selectDocument(docId, { scrollToPara = null } = {}) {
  state.currentDocId = docId;
  renderSidebar();
  let doc = state.docCache[docId];
  if (!doc) {
    const res = await fetch('/api/document?id=' + encodeURIComponent(docId));
    doc = await res.json();
    state.docCache[docId] = doc;
  }
  renderDocument(doc);
  if (scrollToPara !== null) {
    const el = document.getElementById('para-' + scrollToPara);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      document.querySelectorAll('.para.is-current').forEach(p => p.classList.remove('is-current'));
      el.classList.add('is-current');
    }
  }
}

async function loadDocuments() {
  const res = await fetch('/api/documents');
  state.documents = await res.json();
  renderSidebar();
  if (state.documents.length) {
    selectDocument(state.documents[0].id);
  } else {
    docView.innerHTML = '<div class="empty">No documents loaded.</div>';
  }
}

function updateNavButtons() {
  const nav = navigableMatches();
  prevBtn.disabled = nav.length === 0;
  nextBtn.disabled = nav.length === 0;
}

async function goToMatch(delta) {
  const nav = navigableMatches();
  if (nav.length === 0) return;
  state.pointer = (state.pointer + delta + nav.length) % nav.length;
  const match = nav[state.pointer];
  status.textContent = `Match ${state.pointer + 1} of ${nav.length} for "${state.query}"`;
  await selectDocument(match.doc_id, { scrollToPara: match.para_index });
}

async function runSearch(query) {
  state.query = query;
  if (!query) {
    state.matches = []; state.matchesByKey = {}; state.matchesByDoc = {}; state.pointer = -1;
    status.textContent = '';
    updateNavButtons();
    renderSidebar();
    if (state.currentDocId) selectDocument(state.currentDocId);
    return;
  }
  status.textContent = 'Searching…';
  const res = await fetch('/api/search?q=' + encodeURIComponent(query));
  const data = await res.json();
  if (!res.ok) {
    status.textContent = data.error || 'Search failed.';
    return;
  }
  state.matches = data.results;
  state.matchesByKey = {};
  state.matchesByDoc = {};
  for (const m of data.results) {
    if (m.doc_id === null || m.para_index === null) continue;
    state.matchesByKey[m.doc_id + ':' + m.para_index] = m;
    state.matchesByDoc[m.doc_id] = (state.matchesByDoc[m.doc_id] || 0) + 1;
  }
  state.pointer = -1;
  updateNavButtons();
  renderSidebar();
  const nav = navigableMatches();
  if (nav.length > 0) {
    await goToMatch(1);
  } else {
    status.textContent = `No matches for "${query}".`;
    if (state.currentDocId) selectDocument(state.currentDocId);
  }
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  runSearch(input.value.trim());
});
prevBtn.addEventListener('click', () => goToMatch(-1));
nextBtn.addEventListener('click', () => goToMatch(1));

loadDocuments();
</script>
</body>
</html>
"""


def _para_index_from_item(item_label: str) -> int | None:
    """"¶12" -> 11 (0-based index into that document's paragraph list)."""
    if not item_label.startswith("¶"):
        return None
    try:
        return int(item_label[1:]) - 1
    except ValueError:
        return None


def create_app(documents, paragraphs, search_fn, highlight_fn, engine_name: str, top: int) -> Flask:
    app = Flask(__name__)

    doc_ids = list(documents.keys())
    name_to_id = {documents[d].get("name", d): d for d in doc_ids}
    n_paragraphs = sum(len(v) for v in paragraphs.values())

    @app.get("/")
    def index():
        return render_template_string(_PAGE, engine=engine_name, n_docs=len(doc_ids), n_paragraphs=n_paragraphs)

    @app.get("/api/documents")
    def api_documents():
        return jsonify([
            {"id": d, "name": documents[d].get("name", d), "n_paragraphs": len(paragraphs.get(d, []))}
            for d in doc_ids
        ])

    @app.get("/api/document")
    def api_document():
        doc_id = request.args.get("id", "")
        if doc_id not in documents:
            return jsonify({"error": "unknown document id"}), 404
        items = paragraphs.get(doc_id, [])
        return jsonify({
            "id": doc_id,
            "name": documents[doc_id].get("name", doc_id),
            "paragraphs": [{"index": i, "text": it["description"]} for i, it in enumerate(items)],
        })

    @app.get("/api/search")
    def api_search():
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"error": "missing query parameter 'q'"}), 400
        limit = min(int(request.args.get("limit", 500)), 2000)

        raw_results = search_fn(query)
        out = []
        for r in raw_results[:limit]:
            text = r.get("description", "")
            out.append({
                "doc_id": name_to_id.get(r.get("restaurant", "")),
                "doc_name": r.get("restaurant", ""),
                "para_index": _para_index_from_item(r.get("item", "")),
                "excerpt": text,
                "score": r.get("score"),
                "highlights": [list(span) for span in highlight_fn(query, text)] if text else [],
            })
        return jsonify({
            "query": query,
            "engine": engine_name,
            "total": len(raw_results),
            "shown": len(out),
            "results": out[:top] if top else out,
        })

    return app


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Browser UI for grep-like concept search across plain text documents",
        usage="%(prog)s [options] doc [doc ...]",
    )
    parser.add_argument(
        "docs", nargs="+",
        help="Files and/or directories to search (shell globs expand naturally, e.g. data/menus/*.md); "
             "directories are scanned recursively for --ext files",
    )
    add_engine_args(parser)
    parser.add_argument(
        "--top", type=int, default=200,
        help="Max matches sent to the browser per query, across all documents (default: 200)",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Don't automatically open a browser tab")
    args = parser.parse_args()

    try:
        documents, paragraphs, search_fn, highlight_fn = load_engine(args)
    except ValueError as e:
        parser.error(str(e))

    app = create_app(documents, paragraphs, search_fn, highlight_fn, args.engine, args.top)

    url = f"http://127.0.0.1:{args.port}/"
    print(f"\nServing on {url}  (engine: {args.engine}) -- Ctrl+C to stop\n")
    if not args.no_browser:
        webbrowser.open(url)
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
