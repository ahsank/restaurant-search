"""
Approach 5 data generation, variant 2: synthetic (anchor, positive, hard
negative) triples mined purely from menu *structure* across every restaurant
in data/menus/ — no dependency on data/queries/relevance_*.csv at all. This
is a different bet than mine_hard_negatives.py: instead of leaning on the
209-query benchmark's real judgments (small, and requires holding out queries
to avoid leakage — see mine_hard_negatives.py's docstring), it targets three
specific confusion patterns by construction, at whatever scale data/menus/
supports, and can be evaluated against the ENTIRE benchmark with zero leakage
risk since no benchmark data informs training.

Three structural hard-negative patterns:

1. **Specific-modifier confusion** — items sharing a dish-type head noun
   ("sandwich", "taco", "burger", ...) but a different modifier are hard
   negatives for each other: "Chicken Sandwich" vs "Turkey Club Sandwich" vs
   "Veggie Sandwich". A pretrained bi-encoder tends to cluster these as
   near-duplicates; the model needs to learn the modifier is what matters.

2. **Combo/bundle vs standalone** — a combo item naming a *different* core
   dish ("Combo 3: Two Enchiladas") shares generic bundling vocabulary
   ("combo", "meal", numbers) with a query for an unrelated standalone item
   ("chicken sandwich") without actually containing it — attached as an
   extra hard negative onto pattern-1 cases when such a combo exists in the
   same restaurant.

3. **Length-bias negatives** — mirrors the length-normalization failure mode
   already documented in APPROACHES.md's Soft-BM25 "pizza" investigation: a
   long, fully-matching item (e.g. a seafood pasta dish) is paired against a
   short item that shares exactly one concept keyword but is a different
   dish entirely (e.g. a "Clam Dip" appetizer sharing "clam"). Anchors reuse
   Approach 1's example concept thesaurus (seafood/italian/spicy/healthy),
   including the project's own canonical "seafood italian" example.

Patterns 1-2 use `claude -p` (the already-authenticated Claude Code CLI — no
separate ANTHROPIC_API_KEY needed) to turn each case into natural paraphrase
queries, grounded in the specific siblings it must NOT match. Pattern 3's
anchor is already a natural short concept phrase, so it skips the LLM call.

Usage:
    python research/data_gen/generate_synthetic_data.py
    python research/data_gen/generate_synthetic_data.py --skip-llm      # structural mining only, free, for sanity-checking case counts
    python research/data_gen/generate_synthetic_data.py --model claude-haiku-4-5-20251001 --batch-size 20

Output: research/data_gen/synthetic_triples.jsonl — JSONL of
    {"anchor", "positive", "negative", "source"} rows. Any anchor exactly
    matching a real data/queries/queries.csv query_text is dropped, so
    training on this file and evaluating on the full benchmark stays a clean
    train/test split without needing a held-out-query file.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "research"))
from lib.data import load_data

sys.path.insert(0, str(_ROOT / "research" / "search"))
from sbert_search import _item_text
from evaluate import load_queries

_DEFAULT_OUT = Path(__file__).parent / "synthetic_triples.jsonl"
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_BATCH_SIZE = 20

# Dish-type head nouns checked as whole words (singular or plural) against
# lowercased item names. Includes Spanish dish-family words (camarones,
# pollo) since Mexican-restaurant menus here name variants that way — e.g.
# "Camarones a la Diabla" / "Camarones Mojo de Ajo" / "Camarones con Bacon"
# are exactly the specific-modifier-confusion pattern this targets.
DISH_TYPES = [
    "sandwich", "taco", "burger", "burrito", "enchilada", "salad", "pasta",
    "pizza", "soup", "wrap", "bowl", "quesadilla", "nachos", "sundae",
    "omelette", "curry", "noodles", "dumpling", "roll", "skewer", "chowder",
    "risotto", "lasagna", "calzone", "panini", "fajita", "tostada",
    "camarones", "pollo", "chow mein",
]
_STOPWORDS = {"the", "a", "an", "with", "and", "of", "style", "our", "house", "special", "de", "la"}


def _pluralize(word: str) -> str:
    return word + "es" if word.endswith(("ch", "sh", "x", "s", "z")) else word + "s"


def _dish_type_pattern(dish_type: str) -> re.Pattern:
    """Match a dish-type phrase as whole words, singular or plural on the last word."""
    parts = dish_type.split()
    prefix = [re.escape(p) for p in parts[:-1]]
    last_group = f"(?:{re.escape(parts[-1])}|{re.escape(_pluralize(parts[-1]))})"
    pattern = r"\b" + r"\s+".join(prefix + [last_group]) + r"\b"
    return re.compile(pattern)


_DISH_TYPE_PATTERNS = {dt: _dish_type_pattern(dt) for dt in DISH_TYPES}

# Approach 1's example concept thesaurus (APPROACHES.md) — reused here as the
# vocabulary for length-bias anchor/negative detection.
CONCEPT_TERMS = {
    "seafood": {"shrimp", "clam", "clams", "salmon", "cod", "lobster", "scallop", "scallops",
                "crab", "tuna", "oyster", "oysters", "mussel", "mussels", "calamari", "squid",
                "halibut", "dungeness", "shellfish", "fish", "prawn", "prawns"},
    "italian": {"pasta", "spaghetti", "linguine", "risotto", "parmesan", "carbonara",
                "mozzarella", "gnocchi", "marinara", "alfredo", "bolognese", "penne", "fettuccine"},
    "spicy": {"chili", "jalapeno", "jalapeño", "sriracha", "arrabbiata", "cajun",
              "habanero", "spicy", "chipotle"},
    "healthy": {"quinoa", "avocado", "kale", "vegan", "gluten-free", "salad", "greens"},
}
_CONCEPT_ORDER = ["seafood", "italian", "spicy", "healthy"]
_LONG_WORDS = 12
_SHORT_WORDS = 5


# ── Pattern 1: specific-modifier confusion ──────────────────────────────────

def _extract_modifier(name: str, dish_type: str) -> str:
    type_words = set(dish_type.split())
    words = re.findall(r"[a-zA-Z']+", name.lower())
    modifier_words = [w for w in words if w not in type_words and w not in _STOPWORDS]
    return " ".join(modifier_words[:3])


def find_specific_modifier_cases(menus: dict) -> list[dict]:
    cases: list[dict] = []
    for rid, items in menus.items():
        groups: dict[str, list[dict]] = defaultdict(list)
        for item in items:
            name_lower = item["name"].lower()
            for dish_type, pattern in _DISH_TYPE_PATTERNS.items():
                if pattern.search(name_lower):
                    groups[dish_type].append(item)
                    break  # first matching type only

        for dish_type, group_items in groups.items():
            if len(group_items) < 2:
                continue
            for item in group_items:
                modifier = _extract_modifier(item["name"], dish_type)
                if not modifier:
                    continue
                siblings = [it for it in group_items if it["name"] != item["name"]]
                if not siblings:
                    continue
                cases.append({
                    "pattern": "specific_modifier",
                    "restaurant_id": rid,
                    "item": item,
                    "seed_query": f"{modifier} {dish_type}",
                    "negatives": siblings[:3],
                })
    return cases


# ── Pattern 2: combo/bundle vs standalone (attached onto pattern-1 cases) ──

def is_combo(item: dict) -> bool:
    text = f"{item['name']} {item.get('category', '') or ''}".lower()
    if re.search(r"\bcombo\b|\bcombination\b|\bvalue meal\b|\bfamily meal\b", text):
        return True
    if re.search(
        r"^(two|three|four)\b.*\b(tacos?|burritos?|enchiladas?|chalupas?|"
        r"sandwiches?|rellenos?|dumplings?|rolls?)\b",
        item["name"].lower(),
    ):
        return True
    return False


def attach_combo_negatives(cases: list[dict], menus: dict) -> None:
    combo_by_restaurant: dict[str, list[dict]] = defaultdict(list)
    for rid, items in menus.items():
        for item in items:
            if is_combo(item):
                combo_by_restaurant[rid].append(item)

    for case in cases:
        dish_type_words = set(case["seed_query"].split())
        for combo_item in combo_by_restaurant.get(case["restaurant_id"], []):
            combo_words = set(re.findall(r"[a-zA-Z']+", combo_item["name"].lower()))
            if dish_type_words & combo_words:
                continue  # combo actually names this dish/type — not a clean negative
            case["negatives"].append(combo_item)
            break  # one combo negative per case is enough


# ── Pattern 3: length-bias negatives (deterministic anchor, no LLM) ────────

def find_length_bias_cases(menus: dict) -> list[dict]:
    cases: list[dict] = []
    for rid, items in menus.items():
        for item in items:
            words = _item_text(item).lower().split()
            if len(words) < _LONG_WORDS:
                continue
            word_set = set(words)
            matched = [c for c in _CONCEPT_ORDER if CONCEPT_TERMS[c] & word_set]
            if not matched:
                continue
            positive_terms: set[str] = set()
            for c in matched:
                positive_terms |= CONCEPT_TERMS[c]

            for other in items:
                if other["name"] == item["name"]:
                    continue
                other_words = _item_text(other).lower().split()
                if len(other_words) > _SHORT_WORDS:
                    continue
                other_word_set = set(other_words)
                other_matched = {c for c in _CONCEPT_ORDER if CONCEPT_TERMS[c] & other_word_set}
                if (positive_terms & other_word_set) and other_matched != set(matched):
                    cases.append({
                        "pattern": "length_bias",
                        "restaurant_id": rid,
                        "item": item,
                        "seed_query": " ".join(matched),
                        "negatives": [other],
                        "queries": [" ".join(matched)],
                    })
                    break
    return cases


# ── LLM paraphrase generation via `claude -p` ───────────────────────────────

def _call_claude(prompt: str, model: str, cwd: Path) -> str:
    result = subprocess.run(
        ["claude", "-p", "--restricted", "--output-format", "json", "--model", model, prompt],
        capture_output=True, text=True, cwd=str(cwd), timeout=120,
    )
    payload = json.loads(result.stdout)
    return payload.get("result", "")


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def generate_queries_for_cases(cases: list[dict], model: str, batch_size: int) -> None:
    """Mutates each case in place, setting case['queries']."""
    scratch_dir = Path(tempfile.gettempdir())  # avoid this repo's CLAUDE.md / auto-memory context overhead

    for start in range(0, len(cases), batch_size):
        batch = cases[start:start + batch_size]
        lines = [
            "Generate short, natural search queries a hungry restaurant customer",
            "might type to find a SPECIFIC menu item, without matching the similar",
            "sibling items also listed (they name a different dish/protein/style).",
            "Output ONLY a raw JSON object (no markdown fences, no prose) mapping",
            "each numeric id (as a string) to a list of exactly 3 short lowercase",
            "query strings a real user might type (a few words each, not full",
            "sentences) — vary phrasing across the 3 (direct name, ingredient-led,",
            "and a casual/misspelled variant are all good).",
            "",
            "Cases:",
        ]
        for i, case in enumerate(batch):
            item = case["item"]
            sibling_names = ", ".join(n["name"] for n in case["negatives"])
            desc = item.get("description") or ""
            lines.append(
                f'{i}. Target: "{item["name"]}" - {desc}. '
                f"Siblings (do NOT match these): {sibling_names}"
            )
        prompt = "\n".join(lines)

        try:
            raw = _call_claude(prompt, model, scratch_dir)
            parsed = _parse_json_object(raw)
        except Exception as e:
            print(f"\n  [warn] batch at {start} failed ({e}); using seed queries for this batch")
            parsed = {}

        for i, case in enumerate(batch):
            queries = parsed.get(str(i))
            case["queries"] = queries if queries else [case["seed_query"]]

        print(f"  {min(start + batch_size, len(cases))}/{len(cases)} cases", end="\r", flush=True)
    print()


# ── Assembly ─────────────────────────────────────────────────────────────

def build_triples(cases: list[dict]) -> list[dict]:
    triples = []
    for case in cases:
        positive_text = _item_text(case["item"])
        for q in case.get("queries") or [case["seed_query"]]:
            for neg_item in case["negatives"]:
                triples.append({
                    "anchor": q,
                    "positive": positive_text,
                    "negative": _item_text(neg_item),
                    "source": f"synthetic_{case['pattern']}",
                })
    return triples


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    parser.add_argument("--model", default=_DEFAULT_MODEL, help=f"claude -p model (default: {_DEFAULT_MODEL})")
    parser.add_argument("--batch-size", type=int, default=_DEFAULT_BATCH_SIZE,
                        help=f"Cases per claude -p call (default: {_DEFAULT_BATCH_SIZE})")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Structural mining only, using each case's deterministic seed "
                             "query as its anchor — no claude -p calls, free, for sanity-checking "
                             "case counts before spending on generation")
    args = parser.parse_args()

    print("Loading ALL restaurants in data/menus/ (not scoped to judged subset — "
          "synthetic mining needs no relevance judgments)...", end=" ", flush=True)
    restaurants, menus = load_data()
    print(f"{sum(len(v) for v in menus.values())} items across {len(menus)} restaurants")

    modifier_cases = find_specific_modifier_cases(menus)
    attach_combo_negatives(modifier_cases, menus)
    length_bias_cases = find_length_bias_cases(menus)
    print(f"  {len(modifier_cases)} specific-modifier cases, {len(length_bias_cases)} length-bias cases")

    if args.skip_llm:
        for c in modifier_cases:
            c["queries"] = [c["seed_query"]]
    else:
        print(f"Generating paraphrase queries via `claude -p` ({args.model})...")
        generate_queries_for_cases(modifier_cases, args.model, args.batch_size)

    triples = build_triples(modifier_cases + length_bias_cases)

    existing_query_texts = {q["query_text"].strip().lower() for q in load_queries()}
    before = len(triples)
    triples = [t for t in triples if t["anchor"].strip().lower() not in existing_query_texts]
    if before != len(triples):
        print(f"  Dropped {before - len(triples)} triples whose anchor exactly matched a benchmark query")

    seen = set()
    deduped = []
    for t in triples:
        key = (t["anchor"], t["positive"], t["negative"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(t)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for t in deduped:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    by_source: dict[str, int] = defaultdict(int)
    for t in deduped:
        by_source[t["source"]] += 1
    print(f"\nWrote {len(deduped)} triples to {args.out}")
    for source, n in sorted(by_source.items()):
        print(f"  {source}: {n}")
