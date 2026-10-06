"""
Approach 7: local LLM as reader — no training, no index.

For every (query, restaurant) pair the LLM sees that restaurant's whole menu
as a numbered list and returns the matching item numbers, best first, each
graded 2 (highly relevant) or 1 (partially relevant) — the same scale as the
benchmark judgments. One prompt per restaurant keeps the context small (the
largest benchmark menu is ~5K tokens) and lets vLLM's prefix cache reuse the
menu across queries: the menu comes first, the query last.

Merging restaurants into one ranked list: grade first (all 2s before all 1s),
then position within the restaurant's own list, so restaurants interleave
rather than one restaurant's whole list coming first.

Needs a GPU and vLLM, so it is meant to run on Colab — see
research/colab/run_llm_eval.sh, which uploads the code, runs this script on a
GPU VM and downloads the results. The run writes a rankings JSONL that the
local `evaluate.py --engine llm --rankings FILE` replays without a GPU, so
metrics can be re-sliced (by category, difficulty, held-out ids) locally.

Usage (on a GPU machine):
    python research/search/llm_search.py --model Qwen/Qwen2.5-7B-Instruct \\
        --out runs/llm_qwen2.5-7b.jsonl
    python research/search/llm_search.py --limit 5 ...        # smoke test, first 5 queries

Replay locally:
    python research/search/evaluate.py --engine llm --rankings runs/llm_qwen2.5-7b.jsonl
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

SYSTEM_PROMPT = """\
You are a menu search assistant. Given one restaurant's menu and a diner's \
search query, find the menu items that match the query.

Match by meaning, not just by words:
- Ingredients imply categories: shrimp, clams, salmon, cod, crab or any fish \
count as "seafood"; "shellfish" means shrimp, crab, lobster, clams, mussels, \
oysters, scallops.
- Tolerate misspellings, plurals, hyphenation and spacing ("caeser" = \
"caesar", "cacioepepe" = "cacio e pepe").
- Respect constraints: dietary needs (vegetarian, vegan, gluten-free), price \
limits, negations ("no cheese"), meal time or menu (lunch, happy hour), and \
the restaurant's cuisine when the query names one.
- A dish matches a dish-type query ("taco", "soup", "pasta") only if it is \
that kind of dish, not if it merely contains the word.

Grade each match:
2 = clearly what the diner is looking for
1 = partially matches (related, or satisfies only part of the query)

Answer with JSON only, no other text: a list of [item_number, grade] pairs, \
best match first, e.g. [[12, 2], [3, 2], [40, 1]]. Return [] if nothing \
matches. Do not list items that do not match."""


def cli_args() -> argparse.ArgumentParser:
    """--rankings flag fragment for `evaluate.py --engine llm` (see engines.py)."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--rankings", type=Path,
        help="Rankings JSONL written by llm_search.py on a GPU machine; "
             "required for --engine llm, which replays it instead of running the LLM",
    )
    return parser


# ---------------------------------------------------------------------------
# Prompt building / parsing
# ---------------------------------------------------------------------------

def menu_entries(items: list[dict]) -> list[dict]:
    """
    One entry per distinct item name. Several menus repeat a dish (lunch and
    dinner); the benchmark judges by name, so a name is listed once, with
    every menu it appears on.
    """
    entries: dict[str, dict] = {}
    for item in items:
        e = entries.get(item["name"])
        if e is None:
            entries[item["name"]] = {**item, "menu_types": [item["menu_type"]]}
        elif item["menu_type"] not in e["menu_types"]:
            e["menu_types"].append(item["menu_type"])
    return list(entries.values())


def menu_block(restaurant: dict, entries: list[dict]) -> str:
    header = [f"RESTAURANT: {restaurant.get('name', restaurant['id'])}"]
    if restaurant.get("cuisine"):
        header.append(f"Cuisine: {restaurant['cuisine']}")
    lines = []
    for i, e in enumerate(entries, 1):
        line = f"{i}. {e['name']}"
        if e["price_raw"]:
            line += f" — {e['price_raw']}"
        details = [d for d in (e["description"], e["dietary"] and f"Dietary: {e['dietary']}") if d]
        details.append(f"[{e['category'] or 'Menu'}; {', '.join(m for m in e['menu_types'] if m)} menu]")
        lines.append(line + " | " + " | ".join(details))
    return "\n".join(header) + "\n\nMENU:\n" + "\n".join(lines)


def build_messages(query: str, menu: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{menu}\n\nQUERY: {query}"},
    ]


_PAIR = re.compile(r"\[\s*(\d+)\s*,\s*([0-2])\s*\]")


def parse_response(text: str, n_items: int) -> list[tuple[int, int]]:
    """
    Pull [item_number, grade] pairs out of the model's answer, in order.
    Tolerant of code fences and chatter around the JSON; drops out-of-range
    numbers, grade-0 pairs and repeats.
    """
    out: list[tuple[int, int]] = []
    seen: set[int] = set()
    for num, grade in _PAIR.findall(text):
        idx, g = int(num), int(grade)
        if 1 <= idx <= n_items and g > 0 and idx not in seen:
            seen.add(idx)
            out.append((idx, g))
    return out


def merge(per_restaurant: dict[str, list[dict]]) -> list[dict]:
    """
    Combine each restaurant's graded list into one ranking: grade descending,
    then rank within its restaurant, then restaurant order as the final tie-break.
    """
    flat = []
    for r_order, (rid, hits) in enumerate(per_restaurant.items()):
        for pos, h in enumerate(hits):
            flat.append(((-h["grade"], pos, r_order), {"restaurant_id": rid, **h}))
    flat.sort(key=lambda t: t[0])
    return [h for _, h in flat]


# ---------------------------------------------------------------------------
# Batch run (vLLM)
# ---------------------------------------------------------------------------

def run(
    queries: list[dict],
    restaurants: dict,
    menus: dict,
    model_name: str,
    out_path: Path,
    max_model_len: int = 12288,
    max_tokens: int = 768,
    gpu_memory_utilization: float = 0.90,
) -> list[dict]:
    """
    Score every query against every restaurant in one vLLM batch and write one
    JSONL row per query: {query_id, query_text, results: [...], raw: {rid: text}}.
    """
    from vllm import LLM, SamplingParams

    entries = {rid: menu_entries(items) for rid, items in menus.items()}
    blocks = {rid: menu_block(restaurants[rid], entries[rid]) for rid in menus}

    jobs, conversations = [], []
    for q in queries:
        for rid in menus:
            jobs.append((q, rid))
            conversations.append(build_messages(q["query_text"], blocks[rid]))

    llm = LLM(
        model=model_name,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        enable_prefix_caching=True,
    )
    params = SamplingParams(temperature=0.0, max_tokens=max_tokens)

    print(f"{len(queries)} queries x {len(menus)} restaurants = {len(conversations)} prompts", flush=True)
    t0 = time.time()
    outputs = llm.chat(conversations, params, use_tqdm=True)
    elapsed = time.time() - t0
    print(f"Generated in {elapsed:.1f}s ({elapsed / max(len(queries), 1):.2f}s per query)", flush=True)

    rows: dict[str, dict] = {}
    for (q, rid), out in zip(jobs, outputs):
        text = out.outputs[0].text
        row = rows.setdefault(q["query_id"], {
            "query_id": q["query_id"], "query_text": q["query_text"], "per_restaurant": {}, "raw": {},
        })
        row["raw"][rid] = text
        row["per_restaurant"][rid] = [
            {"name": entries[rid][idx - 1]["name"], "grade": grade}
            for idx, grade in parse_response(text, len(entries[rid]))
        ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"meta": {
            "model": model_name, "n_queries": len(queries), "n_prompts": len(conversations),
            "seconds": round(elapsed, 1), "system_prompt": SYSTEM_PROMPT,
        }}) + "\n")
        for row in rows.values():
            row["results"] = merge(row.pop("per_restaurant"))
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path}", flush=True)
    return list(rows.values())


def load_rankings(path: Path) -> dict[str, list[dict]]:
    """{query_text: ranked results} from a rankings JSONL (meta line skipped)."""
    rankings = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if "query_text" in row:
                rankings[row["query_text"]] = row["results"]
    return rankings


def replay_search_fn(path: Path):
    """search_fn(query) for evaluate.py; unknown queries return no results."""
    rankings = load_rankings(path)
    def search(query: str) -> list[dict]:
        return rankings.get(query, [])
    return search


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from evaluate import evaluate, load_queries, print_report

    parser = argparse.ArgumentParser(description="Local LLM reader (Approach 7) over the benchmark")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"HF model id or path (default: {DEFAULT_MODEL})")
    parser.add_argument("--out", type=Path, required=True, help="Rankings JSONL to write")
    parser.add_argument("--limit", type=int, help="Only the first N benchmark queries (smoke test)")
    parser.add_argument("--max-model-len", type=int, default=12288)
    parser.add_argument("--max-tokens", type=int, default=768, help="Max generated tokens per prompt")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    args = parser.parse_args()

    queries = load_queries()[: args.limit] if args.limit else load_queries()
    restaurants, menus = load_data(judged_restaurant_ids())
    run(queries, restaurants, menus, args.model, args.out,
        max_model_len=args.max_model_len, max_tokens=args.max_tokens,
        gpu_memory_utilization=args.gpu_memory_utilization)

    results = evaluate(replay_search_fn(args.out),
                       query_ids={q["query_id"] for q in queries})
    print_report(results)
    metrics_path = args.out.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(
        {k: results[k] for k in ("overall", "by_category", "by_difficulty")}, indent=2))
    print(f"Wrote {metrics_path}")
