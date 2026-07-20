# Search Benchmark

This directory contains the query set and relevance judgments used to evaluate the restaurant menu search engine. Full background on the motivation, challenge taxonomy, and ablation experiment plan is in [`menu-search-benchmark-queries.md`](../../menu-search-benchmark-queries.md) at the project root.

## Files

| File | Description |
|------|-------------|
| `queries.csv` | 100 benchmark queries |
| `relevance_<restaurant-id>.csv` | Relevance judgments for one restaurant, e.g. `relevance_juanita-cantina.csv` |

## `queries.csv` — format

```
query_id,category_id,query_text,difficulty,category_name
1,C01,Mexican food with shrimp,Medium,Cuisine type inference
```

| Column | Values |
|--------|--------|
| `query_id` | 1–100 |
| `category_id` | C01–C10 |
| `query_text` | The raw query string a user might type |
| `difficulty` | `Easy`, `Medium`, or `Hard` |
| `category_name` | Human-readable category label |

### Query categories

Queries 1–100 test search *difficulty*: how well a search engine handles retrieval challenges beyond simple keyword matching. Queries 101–200 are *typical* queries a real user might type, organized by food category.

#### Challenge categories (C01–C10, queries 1–100)

| ID | Name | What it tests |
|----|------|---------------|
| C01 | Cuisine type inference | Dish must be inferred from cuisine label, not item name |
| C02 | Ingredient generalization | Query names a food group; items name specific ingredients |
| C03 | Attribute / implied meaning | Metaphorical or sensory queries ("smoky", "comforting") |
| C04 | Cooking method synonyms | "charbroiled" ↔ "grilled", "wood fired" ↔ "baked" |
| C05 | Spelling variations | Misspellings and phonetic errors ("caeser", "quesedilla") |
| C06 | Stemming & lemmatization | "breading" → "Breaded Calamari", "grilling" → "Grilled Octopus" |
| C07 | Hyphenation / spacing / stop words | "cacio e pepe" vs "cacioepepe", "al pastor" vs "alpastor" |
| C08 | Dietary constraint / negation | "vegan", "no gluten", "nut free" |
| C09 | Synonym / paraphrase | "prawn" → shrimp, "flatbread" → Mexican Pizza |
| C10 | Multi-constraint compositional | Two or more constraints combined |

#### Typical query categories (C11–C23, queries 101–200)

Queries represent what users actually type. A query may name only part of what they want — "beef noodle" not "beef noodle with black bean sauce". Not all components of a dish need to appear in the query for it to be relevant.

| ID | Name | Queries |
|----|------|---------|
| C11 | Soup varieties | 101–107 |
| C12 | Burger varieties | 108–113 |
| C13 | Taco varieties | 114–121 |
| C14 | Pasta varieties | 122–129 |
| C15 | Sandwich varieties | 130–136 |
| C16 | Salad varieties | 137–143 |
| C17 | Dessert varieties | 144–151 |
| C18 | Chicken dishes | 152–157 |
| C19 | Beef dishes | 158–163 |
| C20 | Pork dishes | 164–169 |
| C21 | Seafood dishes | 170–178 |
| C22 | Ingredient focus | 179–188 |
| C23 | Typical dish names | 189–200 |

## `relevance_<restaurant-id>.csv` — format

```
restaurant,query_id,menu_item,relevance
juanita-cantina,1,Camarones à la Diabla,2
juanita-cantina,1,Seafood Enchiladas,1
```

| Column | Values |
|--------|--------|
| `restaurant` | Restaurant ID matching the stem of the `.md` filename |
| `query_id` | Foreign key into `queries.csv` |
| `menu_item` | Name of the item **exactly as it appears** in the `.md` file |
| `relevance` | 0, 1, or 2 (see scale below) |

### Relevance scale

| Value | Meaning |
|-------|---------|
| 2 | Highly relevant — clearly matches the query intent |
| 1 | Partially relevant — related but incomplete match |
| 0 | Not relevant (implicit — omit from file) |

**Sparse format**: only rows with relevance ≥ 1 are stored. Any `(restaurant, query_id, menu_item)` triple not present in the file has implied relevance 0.

### Coverage

Restaurants covered: `due-cucina`, `juanita-cantina`, `mendocino-farms`, `plaza-garcia`, `staple-and-fancy`. The synthetic demo restaurants (`rest_1` through `rest_5`) are excluded from the benchmark.

Not every query has entries for every restaurant — most queries are only relevant to a subset of restaurants. Queries with no entries in any file represent hard cases where no restaurant has a clear match (e.g., query 88 "keto friendly", query 36 "wood fired pizza").

## Exact item name matching

`menu_item` values must exactly match the item name string in the corresponding `.md` file. An evaluation script should look up items by name and treat any unmatched entry as a warning. Known cases to watch for:

- **Accents**: `Camarones à la Diabla` (Juanita Cantina) uses `à` — copy-paste from the md file.
- **Capitalization**: e.g., `Tacos de Pescado` (Juanita) vs `Tacos De Pescado` (Plaza Garcia) — each matches its own md file.
- **Chef's tasting menu items** at Staple & Fancy (e.g., `Little Gem`, `Spring Pea Soup`, `Fried Oysters`) are listed without prices in the md. The parser handles these correctly — `price` is `None` and `price_raw` is `""`. Some items (e.g. `Mezze Rigatoni`, `Hamachi Crudo`) appear in both the chef's menu and the priced dinner menu and will produce two entries.

## Evaluation guidance

### Recommended metrics

- **NDCG@5** — primary metric; rewards ranking highly relevant items at the top
- **Recall@10** — checks breadth; can a search surface all relevant items?
- **MRR** (Mean Reciprocal Rank) — measures how quickly the first relevant result appears

### Stratified analysis

Because `queries.csv` includes `difficulty` and `category_id`, compute per-category and per-difficulty NDCG to diagnose where a search approach falls short (e.g., a BM25 baseline may score well on C05/C06 but fail on C01/C03).

### Evaluation script

See `research/search/evaluate.py` (to be written) for a reference implementation that:
1. Loads all relevance files and the query list
2. Runs a search function against each query
3. Computes NDCG@5, Recall@10, and MRR per query and aggregated by category/difficulty

### Adding new relevance judgments

To add judgments for a new restaurant, create `relevance_<restaurant-id>.csv` — e.g. `relevance_new-place.csv` — with the same header and sparse format. The filename stem after `relevance_` must exactly match the restaurant's markdown file stem (e.g. `new-place.md`). Only include rows where relevance ≥ 1.

To add judgments for a query that currently has none, add rows to the appropriate restaurant file(s). Sort by `query_id` within each file.
