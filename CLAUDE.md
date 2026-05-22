# Restaurant Search

## Project Overview

Semantic menu search for restaurants in the Seattle area (within 50 miles). Users can search across all restaurant menus using natural language queries. A query like `seafood italian` should surface dishes like `CajunPasta` (contains clams, salmon, cod) even though neither word appears in the dish name or description. The search engine will eventually be exposed through a website.

## Architecture

| Layer | Language | Location | Status |
|-------|----------|----------|--------|
| Search engine | C++ | `src/` | In progress |
| Web scraper | Python | `scraper/` | Future |
| Web frontend / API | TBD | `web/` | Future |

## Directory Structure

```
restaurant-search/
├── CMakeLists.txt           # Root CMake build (C++23, GoogleTest)
├── CLAUDE.md
├── data/
│   ├── menus.json           # Menu entries keyed by restaurant_id
│   └── restaurants.json     # Restaurant metadata array
├── src/                     # C++ source
│   ├── search/              # Core search library (CMake target: search)
│   │   ├── search.h
│   │   └── search.cc
│   └── cmd/                 # CLI tools
│       └── searchdemo.cc    # Interactive search demo binary
├── tests/                   # GoogleTest unit tests
│   └── searchtests.cc
├── scraper/                 # Future: Python web scraper
└── web/                     # Future: website / REST API
```

## Data Formats

### `data/restaurants.json`
Array of restaurant objects:
```json
{
  "id": "rest_1",
  "name": "Bella Italia",
  "address": "123 Main St",
  "city": "Seattle",
  "state": "WA",
  "latitude": 47.6062,
  "longitude": -122.3321,
  "cuisine_type": ["italian", "pizza", "pasta"],
  "price_range": "$$",
  "rating": 4.5,
  "review_count": 342,
  "source": "demo"
}
```

### `data/menus.json`
Object keyed by `restaurant_id`, each value is an array of menu items:
```json
{
  "rest_1": [
    {
      "name": "Spaghetti Carbonara",
      "description": "Traditional Roman pasta with eggs, pecorino cheese, and guanciale",
      "price": 16.99,
      "category": "Pasta",
      "dietary_info": [],
      "restaurant_id": "rest_1"
    }
  ]
}
```

## Search Requirements

### Semantic Search (core requirement)

Queries must match dishes by **concept**, not by keyword substring. Examples:

| Query | Must surface | Why |
|-------|-------------|-----|
| `seafood italian` | CajunPasta (rest_1) | Contains clams, salmon, cod — seafood ingredients in an Italian pasta |
| `seafood` | Pad Thai (rest_3) | Contains shrimp |
| `spicy noodles` | Pad Thai, Tom Yum | Noodles + spicy classification |
| `healthy vegetarian` | Quinoa Buddha Bowl, Vegan Caesar Salad | Concept match on health/veg |

Simple substring / keyword matching is insufficient. The search engine must expand query terms to related concepts (e.g., "seafood" → shrimp, clams, salmon, cod, lobster, scallops).

Possible approaches (in increasing sophistication):
1. **Concept thesaurus**: hardcoded or data-driven mapping of query terms to ingredient/category synonyms
2. **TF-IDF + query expansion**: index all menu text, expand query with related terms
3. **Embedding-based search**: encode menu items and queries as vectors, rank by cosine similarity

### Search API (C++ library `src/search/`)

The library must:
- Load restaurant and menu data from the JSON files in `data/`
- Accept a free-text query string
- Return ranked menu entries with associated restaurant info
- Be callable from the `searchdemo` CLI and later from a web API wrapper

### CLI Demo (`src/cmd/searchdemo.cc`)

Reads `data/menus.json` and `data/restaurants.json`, accepts a query on the command line or stdin, and prints matching menu items with restaurant names and prices.

## Build

Requires CMake 3.5+, a C++23-capable compiler. GoogleTest is fetched automatically via `FetchContent`.

```bash
cmake -B build
cmake --build build
ctest --test-dir build
```

## Future: Python Scraper (`scraper/`)

Will scrape restaurant menus from public web sources. Output must conform to the `data/menus.json` and `data/restaurants.json` schemas so the C++ search engine can consume scraped data directly. Target: all restaurants within 50 miles of Seattle.

## Future: Website (`web/`)

Will expose the C++ search library through a REST API and serve a search UI. The search API will accept a query string and return ranked menu results with restaurant metadata.
