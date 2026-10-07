# Search Benchmark

This directory contains the query set and relevance judgments used to evaluate the restaurant menu search engine. Full background on the motivation, challenge taxonomy, and ablation experiment plan is in [`menu-search-benchmark-queries.md`](../../menu-search-benchmark-queries.md) at the project root.

## Files

| File | Description |
|------|-------------|
| `queries.csv` | 209 benchmark queries |
| `relevance_<restaurant-id>.csv` | Relevance judgments for one restaurant, e.g. `relevance_juanita-cantina.csv` |

## `queries.csv` — format

```
query_id,category_id,query_text,difficulty,category_name
C01-01,C01,Mexican food with shrimp,Medium,Cuisine type inference
```

| Column | Values |
|--------|--------|
| `query_id` | `{category_id}-{seq}`, e.g. `C01-01`, `C14-09` — stable per category, see below |
| `category_id` | C01–C25 |
| `query_text` | The raw query string a user might type |
| `difficulty` | `Easy`, `Medium`, or `Hard` |
| `category_name` | Human-readable category label |

### `query_id` scheme

`query_id` is `{category_id}-{two-digit sequence within that category}`, not a global
counter. This means **adding a new query to an existing category never requires
renumbering any other row** — a new C14 (Pasta) query just becomes `C14-09`,
appended after the existing `C14-01`..`C14-08`; every other category's IDs are
untouched. This also keeps `relevance_*.csv` files stable: a query's ID never
changes once assigned, so old relevance judgments never need remapping when the
query set grows.

(Older versions of this benchmark used a flat global integer 1–204. That scheme
was migrated to the category-seq format so future insertions wouldn't require
renumbering every downstream row across all 8 CSV files. `evaluate.py` treats
`query_id` as an opaque string key throughout, so the format change required no
code changes.)

### Query categories

C01–C10 test search *difficulty*: how well a search engine handles retrieval challenges beyond simple keyword matching. C11–C25 are *typical* queries a real user might type, organized by food category or occasion.

#### Challenge categories (C01–C10)

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

#### Typical query categories (C11–C25)

Queries represent what users actually type. A query may name only part of what they want — "beef noodle" not "beef noodle with black bean sauce". Not all components of a dish need to appear in the query for it to be relevant.

| ID | Name | Queries |
|----|------|---------|
| C11 | Soup varieties | C11-01..C11-07 |
| C12 | Burger varieties | C12-01..C12-06 |
| C13 | Taco varieties | C13-01..C13-08 |
| C14 | Pasta varieties | C14-01..C14-08 |
| C15 | Sandwich varieties | C15-01..C15-07 |
| C16 | Salad varieties | C16-01..C16-07 |
| C17 | Dessert varieties | C17-01..C17-08 |
| C18 | Chicken dishes | C18-01..C18-06 |
| C19 | Beef dishes | C19-01..C19-06 |
| C20 | Pork dishes | C20-01..C20-06 |
| C21 | Seafood dishes | C21-01..C21-09 |
| C22 | Ingredient focus | C22-01..C22-13 |
| C23 | Typical dish names | C23-01..C23-12 |
| C24 | Pizza varieties | C24-01..C24-03 |
| C25 | Occasion / meal-time | C25-01..C25-02 |

## `relevance_<restaurant-id>.csv` — format

```
restaurant,query_id,menu_item,relevance
juanita-cantina,C01-01,Camarones à la Diabla,2
juanita-cantina,C01-01,Seafood Enchiladas,1
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

Restaurants covered: `anthonys-homeport`, `due-cucina`, `great-china-restaurant`, `juanita-cantina`, `mendocino-farms`, `plaza-garcia`, `rimini-restaurant`, `staple-and-fancy`. (`bella-italia`, a fictional demo restaurant, was removed in October 2026 and replaced by `rimini-restaurant`.)

Not every query has entries for every restaurant — most queries are only relevant to a subset of restaurants. Queries with no entries in any file represent hard cases where no restaurant has a clear match (e.g., `C08-10` "keto friendly", `C04-06` "wood fired pizza").

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

See `research/search/evaluate.py` for a reference implementation that:
1. Loads all relevance files and the query list
2. Runs a search function against each query
3. Computes NDCG@5, Recall@10, and MRR per query and aggregated by category/difficulty

### Label review log

`label_review_2026-10.csv` lists judgments added in the October 2026 review,
with the reason for each. The review covered items that the Qwen2.5-7B run
(`research/results/llm/qwen2.5-7b-instruct.jsonl`) returned for a query but
that had no judgment here. Each one was checked against the query intent in
`menu-search-benchmark-queries.md`, and those found relevant were added
(1,494 → 1,864 judgments; 1,816 after Bella Italia was removed, 2,101 after Rimini Restaurant was added). Existing judgments were not changed or removed.
A follow-up check of three C01 queries added 6 missed judgments (2,107) and
fixed nine Juanita Cantina rows spelled `Tacos De Pescado`, which never matched
the menu's `Tacos de Pescado` and so counted as 0; both are in the log too.
A pork pass then added 67 judgments (2,174), mostly to C20 Pork dishes: items
with pork as the main protein got 2; items with pork as a component, side, or
one of several meat choices got 1. Molcajete was also added to C01-01.

### Adding new relevance judgments

To add judgments for a new restaurant, create `relevance_<restaurant-id>.csv` — e.g. `relevance_new-place.csv` — with the same header and sparse format. The filename stem after `relevance_` must exactly match the restaurant's markdown file stem (e.g. `new-place.md`). Only include rows where relevance ≥ 1.

To add a new query to an existing category, append it to `queries.csv` with the
next unused `{category_id}-{seq}` (e.g. the next query after `C14-08` is
`C14-09`) — no other row in `queries.csv` or any `relevance_*.csv` needs to
change. To add a new category, pick the next unused `C` number and start its
sequence at `-01`.

Sort by `query_id` within each file (this groups by category, then by sequence, since IDs are zero-padded strings).

To add judgments for a query that currently has none, add rows to the appropriate restaurant file(s). Sort by `query_id` within each file.
