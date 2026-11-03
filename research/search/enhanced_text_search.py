"""
Enhanced text search — improves recall and precision over basic text search
by scoring items across multiple match tiers and including restaurant/menu context.

Features:
  - Token-level matching: uses normalized word-boundary token matching to avoid
    spurious substring matches (e.g. 'tea' in 'steak', 'pie' in 'piece').
  - Hyphen and slash normalization: converts hyphens and slashes to spaces in both
    queries and indexed fields (e.g. 'farm-to-table' matches 'farm to table').
  - Dynamic Levenshtein spelling tolerance: when a query term has no exact match
    (including singular/plural variants) in the corpus vocabulary, automatically finds
    the closest corpus terms within edit distance <= 1 (for length >= 4) or <= 2
    (for length >= 6), tie-breaking by corpus frequency.
  - IDF-weighted partial scoring: replaces rigid all-or-nothing matching with
    smooth IDF-weighted per-term scoring across tiers:
      - Term in item name         → weight 4 × IDF
      - Term in item description  → weight 2 × IDF
      - Term in context fields    → weight 1 × IDF
        (category, menu type, dietary, price_raw, restaurant name, cuisine, description)
  - Match bonuses:
      - All query terms matched anywhere in item/context  → +15 bonus
      - All query terms matched in item name alone       → +10 bonus
      - Full normalized query == normalized item name    → score 1000 (exact match)

Filtered mode (filter_restaurant_ctx=True):
  Before matching a query term against restaurant-level context (cuisine,
  restaurant description), check whether the term already appears anywhere in
  that restaurant's menu (item names, descriptions, categories, menu types, dietary, price).
  If it does, skip the restaurant-level match — item-level matching handles it.
  This prevents a label like "pasta" in `cuisine: italian, pasta, sandwiches`
  from surfacing every item in the restaurant for a "pasta" query.

Accent normalization: diacritics are stripped before comparison so that
"camarones a la diabla" matches "Camarones à la Diabla".

Results are returned sorted by score descending; items with score 0 are excluded.

Usage:
    python enhanced_text_search.py seafood
    python enhanced_text_search.py spicy pasta
    python enhanced_text_search.py --filtered pasta
"""
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args

STOP_WORDS = {
    "a", "an", "the",
    "and", "or", "&",
    "with", "in", "on", "at", "to", "for", "of", "by", "from",
    "as", "into", "over", "after", "before", "between", "under", "about", "through",
    "is", "are", "was", "were", "be", "been", "being",
    "it", "its", "that", "this", "these", "those",
}


def normalize(text: str) -> str:
    """Lowercase, strip combining diacritics, and normalize hyphens/slashes to spaces."""
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c)).lower()
    return re.sub(r"[-/]+", " ", cleaned)


def tokenize(text: str) -> list[str]:
    """Tokenize normalized text into alphanumeric words."""
    return re.findall(r"[a-z0-9]+", normalize(text))


def min_edit_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if not s2:
        return len(s1)

    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, 1):
        curr = [i] + [0] * len(s2)
        for j, c2 in enumerate(s2, 1):
            cost = 0 if c1 == c2 else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[len(s2)]


def term_variants(term: str) -> set[str]:
    """Return the term itself plus basic singular/plural variants."""
    variants = {term}
    # Plural -> singular
    if len(term) > 3:
        if term.endswith("ies") and len(term) > 4:
            variants.add(term[:-3] + "y")  # berries -> berry, fries -> fry
            variants.add(term[:-1])        # cookies -> cookie
        elif term.endswith("ves") and len(term) > 4:
            variants.add(term[:-3] + "f")   # leaves -> leaf, loaves -> loaf
            variants.add(term[:-3] + "fe")  # knives -> knife
        elif term.endswith("es") and len(term) > 3:
            if term.endswith(("shes", "ches", "sses", "xes", "zes")):
                variants.add(term[:-2])     # dishes -> dish, sandwiches -> sandwich, glasses -> glass
            elif term.endswith("oes"):
                variants.add(term[:-2])     # tomatoes -> tomato, potatoes -> potato
                variants.add(term[:-1])
            else:
                variants.add(term[:-1])     # plates -> plate, casseroles -> casserole
                variants.add(term[:-2])
        elif term.endswith("s") and not term.endswith(("ss", "us", "is")):
            variants.add(term[:-1])         # tacos -> taco, burgers -> burger, salads -> salad

    # Singular -> plural
    if len(term) > 2 and (not term.endswith("s") or term.endswith("ss")):
        if term.endswith("y") and len(term) >= 3 and term[-2] not in "aeiou":
            variants.add(term[:-1] + "ies")  # fry -> fries, berry -> berries, curry -> curries
        elif term.endswith(("sh", "ch", "ss", "x", "z")):
            variants.add(term + "es")        # dish -> dishes, sandwich -> sandwiches, glass -> glasses
        elif term.endswith("f") and len(term) > 3:
            variants.add(term[:-1] + "ves")  # loaf -> loaves, leaf -> leaves
            variants.add(term + "s")
        elif term.endswith("fe") and len(term) > 3:
            variants.add(term[:-2] + "ves")  # knife -> knives
            variants.add(term + "s")
        elif term.endswith("o") and len(term) > 3:
            variants.add(term + "es")        # tomato -> tomatoes, potato -> potatoes, taco -> tacos
            variants.add(term + "s")
        else:
            variants.add(term + "s")

    return {v for v in variants if v}


def build_menu_vocab(menus: dict) -> dict[str, set[str]]:
    """
    Per-restaurant set of all words appearing in item names, descriptions,
    categories, menu types, dietary annotations, and price. Used to suppress
    restaurant-level context matching for terms already findable via item-level matching.
    """
    vocab: dict[str, set[str]] = {}
    for restaurant_id, items in menus.items():
        words: set[str] = set()
        for item in items:
            for field in (
                item.get("name") or "",
                item.get("description") or "",
                item.get("category") or "",
                item.get("menu_type") or "",
                item.get("dietary") or "",
                item.get("price_raw") or "",
            ):
                for token in tokenize(field):
                    words.add(token)
                    words.update(term_variants(token))
        vocab[restaurant_id] = words
    return vocab


_CORPUS_CACHE: dict = {}


def _get_corpus_index(menus: dict, restaurants: dict) -> tuple[set[str], Counter, int]:
    """Cache and return (vocab, doc_freq, total_docs) across menus and restaurants."""
    cache_key = (id(menus), id(restaurants))
    if cache_key in _CORPUS_CACHE:
        return _CORPUS_CACHE[cache_key]

    doc_freq: Counter[str] = Counter()
    total_docs = sum(len(items) for items in menus.values())

    for rid, items in menus.items():
        rest = restaurants.get(rid, {})
        r_text = f"{rest.get('name', '')} {rest.get('cuisine', '')} {rest.get('description', '')}"
        r_words = set(tokenize(r_text))
        for item in items:
            item_text = (
                f"{item.get('name') or ''} "
                f"{item.get('description') or ''} "
                f"{item.get('category') or ''} "
                f"{item.get('menu_type') or ''} "
                f"{item.get('dietary') or ''} "
                f"{item.get('price_raw') or ''}"
            )
            item_words = set(tokenize(item_text)) | r_words
            doc_freq.update(item_words)

    vocab = set(doc_freq.keys())
    entry = (vocab, doc_freq, total_docs)
    _CORPUS_CACHE[cache_key] = entry
    return entry


def _compute_idf(term: str, doc_freq: Counter, total_docs: int) -> float:
    n = doc_freq.get(term, 0)
    return math.log(1.0 + (total_docs - n + 0.5) / (n + 0.5))


def _prepare_query_terms(
    query: str,
    vocab: set[str],
    doc_freq: Counter,
    total_docs: int,
) -> tuple[str, list[tuple[str, set[str], float]]]:
    """
    Parse query into terms, applying stop-word filtering, plural/singular variants,
    Levenshtein spelling correction against corpus vocab when no exact match exists,
    and term IDF weights.
    """
    query_norm = normalize(query)
    raw_terms = tokenize(query_norm)
    terms = [t for t in raw_terms if t not in STOP_WORDS] or raw_terms

    term_data = []
    for t in terms:
        variants = term_variants(t)
        term_idf = _compute_idf(t, doc_freq, total_docs)

        # Dynamic Levenshtein spelling tolerance when no exact match in corpus vocab
        if not any(v in vocab for v in variants):
            max_d = 2 if len(t) >= 6 else (1 if len(t) >= 4 else 0)
            if max_d > 0:
                candidates = []
                for w in vocab:
                    if abs(len(w) - len(t)) <= max_d:
                        d = min_edit_distance(t, w)
                        if d <= max_d:
                            candidates.append((d, -doc_freq[w], w))
                if candidates:
                    candidates.sort()
                    best_w = candidates[0][2]
                    variants.update(term_variants(best_w))
                    term_idf = _compute_idf(best_w, doc_freq, total_docs)

        term_data.append((t, variants, term_idf))

    return query_norm, term_data


def _score_item(
    query_terms: list[str],
    query_norm: str,
    item: dict,
    restaurant: dict,
    menu_vocab: set[str] | None = None,
    term_data: list[tuple[str, set[str], float]] | None = None,
    all_terms_bonus: float = 15.0,
) -> float:
    name_norm = normalize(item.get("name") or "")
    if query_norm.strip() == name_norm.strip():
        return 1000.0

    if term_data is None:
        terms = [t for t in query_terms if t not in STOP_WORDS] or query_terms
        term_data = [(t, term_variants(t), 1.0) for t in terms]

    if not term_data:
        return 0.0

    name_tokens = set(tokenize(item.get("name") or ""))
    desc_tokens = set(tokenize(item.get("description") or ""))
    item_ctx_tokens = (
        set(tokenize(item.get("category") or ""))
        | set(tokenize(item.get("menu_type") or ""))
        | set(tokenize(item.get("dietary") or ""))
        | set(tokenize(item.get("price_raw") or ""))
    )

    rest_dict = restaurant or {}
    r_name_tokens = set(tokenize(rest_dict.get("name", "")))
    r_other_tokens = set(tokenize(rest_dict.get("cuisine", ""))) | set(tokenize(rest_dict.get("description", "")))

    name_hits = 0
    desc_hits = 0
    ctx_hits = 0
    term_score = 0.0

    for t, variants, term_idf in term_data:
        if variants & name_tokens:
            name_hits += 1
            term_score += 4.0 * term_idf
        elif variants & desc_tokens:
            desc_hits += 1
            term_score += 2.0 * term_idf
        elif (variants & item_ctx_tokens) or (variants & r_name_tokens):
            ctx_hits += 1
            term_score += 1.0 * term_idf
        elif variants & r_other_tokens:
            if menu_vocab is None or not (variants & menu_vocab):
                ctx_hits += 1
                term_score += 1.0 * term_idf

    total_hits = name_hits + desc_hits + ctx_hits
    if total_hits == 0:
        return 0.0

    score = term_score
    if total_hits == len(term_data):
        score += all_terms_bonus
    if name_hits == len(term_data):
        score += 10.0

    return score


def search(
    query: str,
    restaurants: dict,
    menus: dict,
    filter_restaurant_ctx: bool = False,
) -> list[dict]:
    vocab, doc_freq, total_docs = _get_corpus_index(menus, restaurants)
    query_norm, term_data = _prepare_query_terms(query, vocab, doc_freq, total_docs)
    query_terms = [t for t, _, _ in term_data]
    rest_vocabs = build_menu_vocab(menus) if filter_restaurant_ctx else {}

    scored: list[tuple[float, dict]] = []

    for restaurant_id, items in menus.items():
        restaurant = restaurants.get(restaurant_id, {})
        restaurant_name = restaurant.get("name", restaurant_id)
        menu_vocab = rest_vocabs.get(restaurant_id) if filter_restaurant_ctx else None

        for item in items:
            score = _score_item(
                query_terms,
                query_norm,
                item,
                restaurant,
                menu_vocab=menu_vocab,
                term_data=term_data,
            )
            if score > 0:
                scored.append((score, {
                    "restaurant": restaurant_name,
                    "item": item["name"],
                    "description": item["description"],
                    "price": item["price"],
                    "price_raw": item["price_raw"],
                    "category": item["category"],
                    "menu_type": item["menu_type"],
                    "dietary": item.get("dietary", ""),
                    "score": round(score, 2),
                }))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [r for _, r in scored]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[restaurant_scope_cli_args()])
    parser.add_argument("--filtered", action="store_true",
                        help="Filter restaurant context by menu vocabulary")
    parser.add_argument("terms", nargs="+")
    args = parser.parse_args()

    query = " ".join(args.terms)
    restaurants, menus = load_data(judged_restaurant_ids())
    results = search(query, restaurants, menus, filter_restaurant_ctx=args.filtered)

    mode = "filtered" if args.filtered else "unfiltered"
    print(f"Query: '{query}'  [{mode}]  —  {len(results)} match(es)\n")
    for r in results:
        price_str = f"${r['price']:.2f}" if r["price"] is not None else (r["price_raw"] or "N/A")
        dietary_str = f" ({r['dietary']})" if r.get("dietary") else ""
        print(
            f"  [{r['score']:>5.1f}] {r['restaurant']} | {r['item']}  {price_str}"
            f"  [{r['category']} · {r['menu_type']}]{dietary_str}"
        )
        if r["description"]:
            print(f"       {r['description']}")
        print()
