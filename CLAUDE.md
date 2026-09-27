# Restaurant Search

## Project Overview

Semantic menu search for restaurants in the Seattle area (within 50 miles). Users can search across all restaurant menus using natural language queries. A query like `seafood italian` should surface dishes like `CajunPasta` (contains clams, salmon, cod) even though neither word appears in the dish name or description. The search engine will eventually be exposed through a website.

## Architecture

| Layer | Language | Location | Status |
|-------|----------|----------|--------|
| Search experimentation | Python | `research/` | Active |
| Search engine (production) | C++ | `src/` | Future |
| Web scraper | Python | `scraper/` | Future |
| Web frontend / API | TBD | `web/` | Future |

## Directory Structure

```
restaurant-search/
├── CLAUDE.md
├── data/
│   ├── menus/               # One .md per restaurant — restaurant info + all menus
│   └── dump/                # Raw source files (PDFs, copy-pasted text, etc.)
├── research/                # Python search experimentation (active)
│   ├── APPROACHES.md        # Search strategy options and trade-offs
│   ├── lib/                 # Shared data loading utilities
│   └── search/              # Search experiment scripts
├── src/                     # Future: C++ production search engine
├── scraper/                 # Future: Python web scraper
└── web/                     # Future: website / REST API
```

## Data Formats

### Markdown restaurant documents (`data/menus/<restaurant-id>.md`)
Each `.md` file represents a single restaurant: it contains the restaurant's metadata (name, address, cuisine, price range, etc.) followed by one or more menus. This makes each file a self-contained document for search — no join with a separate restaurants file is needed. Keeping everything in one place also makes it easy to add a new restaurant by dropping a single file.

Markdown is preferred over JSON for search experiments because it preserves the original menu wording in free-form text, which is important for semantic and embedding-based retrieval. JSON files remain available for structured access but are not the search target.

Convention:
- `#` for the restaurant name.
- Known metadata as plain `Key: value` lines directly below the title — no heading. Only include fields that are actually known; omit anything absent or N/A. Common fields: `Address`, `City`, `Phone`, `Cuisine`, `Price`, `Rating`, `Source`, `Description` (one-sentence to one-paragraph summary of the restaurant's character and cuisine).
- `##` is reserved exclusively for menu types: `## Menu Type: Dinner`.
- `###` for menu categories within a menu type.
- Each item as `- Name — $price` with description and dietary info as indented continuation lines (not sub-bullets). Omit the `Dietary:` line entirely when there is no meaningful dietary information.

```markdown
# Due' Cucina

City: Kirkland, WA
Cuisine: italian, pasta, sandwiches
Price: $$
Source: manual-pdf

## Menu Type: Dinner

### Homemade Pasta
- Zozzona — $15.90
  Homemade pasta with guanciale, sausage, egg yolk and tomato sauce.
  Dietary: gluten-free on request; contains egg, pork, dairy
- Pomodoro — $12.90
  Homemade pasta with fresh tomato sauce.
  Dietary: vegan on request; gluten-free on request
- Kid Red Sauce Pasta — $7.90
  Kids pasta with tomato sauce, served with juice.
```

## Search

### Goal

Queries must match dishes by **concept**, not by keyword substring. Examples:

| Query | Must surface | Why |
|-------|-------------|-----|
| `seafood italian` | CajunPasta (rest_1) | Contains clams, salmon, cod — seafood ingredients in an Italian pasta |
| `seafood` | Pad Thai (rest_3) | Contains shrimp |
| `spicy noodles` | Pad Thai, Tom Yum | Noodles + spicy classification |
| `healthy vegetarian` | Quinoa Buddha Bowl, Vegan Caesar Salad | Concept match on health/veg |

### Current focus: Python experimentation (`research/`)

All search work is done in Python under `research/`. Experiments read the markdown menu files in `data/menus/` directly. See [`research/APPROACHES.md`](research/APPROACHES.md) for a full discussion of search strategies — from a simple concept thesaurus through BM25, word embeddings, sentence transformers, and LLM-based retrieval — with trade-offs and recommended experimentation order. See [`research/COMMANDS.md`](research/COMMANDS.md) for example command lines for every script.

### Benchmark (`data/queries/`)

A 209-query benchmark with relevance judgments for 7 restaurants (Due' Cucina, Juanita Cantina, Mendocino Farms, Plaza Garcia, Staple & Fancy, Bella Italia, Great China Restaurant). See [`data/queries/README.md`](data/queries/README.md) for format details.

Key files:
- `data/queries/queries.csv` — 209 queries with `category_id`, `difficulty`, and `category_name`. `query_id` is `{category_id}-{seq}` (e.g. `C14-03`), stable per category so adding a query never renumbers others.
- `data/queries/relevance_<restaurant-id>.csv` — sparse relevance judgments (only relevance ≥ 1 stored; missing = 0)
- `menu-search-benchmark-queries.md` — full documentation of the 25 query categories and challenge design
- `research/search/evaluate.py` — script to compute NDCG@5, Recall@10, MRR against any search function

**Relevance scale**: 0 = not relevant (implicit), 1 = partially relevant, 2 = highly relevant.

Primary metric: **NDCG@5**. Stratify by `category_id` and `difficulty` to diagnose where a search approach falls short.

## Future: Production Search Engine (`src/`)

C++ library that loads menu data and serves ranked results. Trained models from the Python experiments (Approaches 4–6 in APPROACHES.md) will be exported to ONNX and loaded via ONNX Runtime so the C++ engine stays dependency-free.

Requires CMake 3.5+, a C++23-capable compiler. GoogleTest is fetched automatically via `FetchContent`.

```bash
cmake -B build
cmake --build build
ctest --test-dir build
```

## Future: Web Scraper (`scraper/`)

Will scrape restaurant menus from public web sources. Output must conform to the markdown and JSON schemas in `data/` so the search engine can consume scraped data directly. Target: all restaurants within 50 miles of Seattle.

## Future: Website (`web/`)

Will expose the search engine through a REST API and serve a search UI. The search API will accept a query string and return ranked menu results with restaurant metadata.
