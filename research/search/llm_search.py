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
# Generation: in-process vLLM (batch runs) or a running server (interactive)
# ---------------------------------------------------------------------------

def load_llm(
    model_name: str = DEFAULT_MODEL,
    max_model_len: int = 12288,
    gpu_memory_utilization: float = 0.90,
):
    """vLLM engine with prefix caching (each menu is a shared prompt prefix)."""
    from vllm import LLM
    return LLM(
        model=model_name,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        enable_prefix_caching=True,
    )


class ServerLLM:
    """
    Client for an OpenAI-compatible chat server that already has the model
    loaded: `vllm serve` (see research/colab/llm_server.sh) or `ollama serve`
    (base URL http://localhost:11434). Requests go out in parallel; the server
    batches them and reuses each menu's cached prefix. Stdlib only.

    Ollama ignores context-size options sent over this API, so start it with
    OLLAMA_CONTEXT_LENGTH=16384 or the longest menus get silently truncated.
    """

    def __init__(self, base_url: str = "http://localhost:8000", model: str | None = None,
                 workers: int = 16, timeout: float = 300):
        self.base_url = base_url.rstrip("/")
        self.workers, self.timeout = workers, timeout
        self.model = model or self._request("/v1/models")["data"][0]["id"]

    def _request(self, path: str, body: dict | None = None) -> dict:
        import urllib.request
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def complete(self, conversations: list[list[dict]], max_tokens: int) -> list[str]:
        from concurrent.futures import ThreadPoolExecutor

        def one(messages):
            out = self._request("/v1/chat/completions", {
                "model": self.model, "messages": messages,
                "temperature": 0.0, "max_tokens": max_tokens,
            })
            return out["choices"][0]["message"]["content"]

        with ThreadPoolExecutor(self.workers) as pool:
            return list(pool.map(one, conversations))


def _complete(llm, conversations: list[list[dict]], max_tokens: int) -> list[str]:
    """Generated text per conversation, from a ServerLLM or an in-process vLLM engine."""
    if isinstance(llm, ServerLLM):
        return llm.complete(conversations, max_tokens)
    from vllm import SamplingParams
    params = SamplingParams(temperature=0.0, max_tokens=max_tokens)
    outputs = llm.chat(conversations, params, use_tqdm=len(conversations) > 50)
    return [o.outputs[0].text for o in outputs]


def rank_queries(
    llm,
    queries: list[dict],
    restaurants: dict,
    menus: dict,
    max_tokens: int = 768,
) -> list[dict]:
    """
    Score every query against every restaurant in one batch. llm is an
    in-process vLLM engine (load_llm) or a ServerLLM. queries are dicts with
    "query_id" and "query_text" (evaluate.load_queries() rows).
    Returns one row per query: {query_id, query_text, results: [...], raw: {rid: text}}.
    """
    entries = {rid: menu_entries(items) for rid, items in menus.items()}
    blocks = {rid: menu_block(restaurants[rid], entries[rid]) for rid in menus}

    jobs, conversations = [], []
    for q in queries:
        for rid in menus:
            jobs.append((q, rid))
            conversations.append(build_messages(q["query_text"], blocks[rid]))

    texts = _complete(llm, conversations, max_tokens)

    rows: dict[str, dict] = {}
    for (q, rid), text in zip(jobs, texts):
        row = rows.setdefault(q["query_id"], {
            "query_id": q["query_id"], "query_text": q["query_text"], "per_restaurant": {}, "raw": {},
        })
        row["raw"][rid] = text
        row["per_restaurant"][rid] = [
            {"name": entries[rid][idx - 1]["name"], "grade": grade}
            for idx, grade in parse_response(text, len(entries[rid]))
        ]
    for row in rows.values():
        row["results"] = merge(row.pop("per_restaurant"))
    return list(rows.values())


def search(query: str, llm, restaurants: dict, menus: dict) -> list[dict]:
    """Ad-hoc single query (e.g. from a notebook); same ranking as the benchmark run."""
    return rank_queries(llm, [{"query_id": "adhoc", "query_text": query}], restaurants, menus)[0]["results"]


def run(
    queries: list[dict],
    restaurants: dict,
    menus: dict,
    model_name: str,
    out_path: Path,
    max_model_len: int = 12288,
    max_tokens: int = 768,
    gpu_memory_utilization: float = 0.90,
    llm=None,
) -> list[dict]:
    """rank_queries() over the benchmark, written as a rankings JSONL (meta line first)."""
    if llm is None:
        llm = load_llm(model_name, max_model_len, gpu_memory_utilization)

    n_prompts = len(queries) * len(menus)
    print(f"{len(queries)} queries x {len(menus)} restaurants = {n_prompts} prompts", flush=True)
    t0 = time.time()
    rows = rank_queries(llm, queries, restaurants, menus, max_tokens=max_tokens)
    elapsed = time.time() - t0
    print(f"Generated in {elapsed:.1f}s ({elapsed / max(len(queries), 1):.2f}s per query)", flush=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"meta": {
            "model": model_name, "n_queries": len(queries), "n_prompts": n_prompts,
            "seconds": round(elapsed, 1), "system_prompt": SYSTEM_PROMPT,
        }}) + "\n")
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path}", flush=True)
    return rows


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


def print_results(results: list[dict], restaurants: dict, k: int = 15) -> None:
    for i, r in enumerate(results[:k], 1):
        print(f"  {i:>2}. [{r['grade']}] {r['name']}  ·  {restaurants[r['restaurant_id']].get('name', r['restaurant_id'])}")
    if not results:
        print("  (no matches)")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from evaluate import evaluate, load_queries, print_report

    parser = argparse.ArgumentParser(
        description="Local LLM reader (Approach 7): ad-hoc query, or the full benchmark with --out")
    parser.add_argument("terms", nargs="*", help="Query words for an ad-hoc search (omit to run the benchmark)")
    parser.add_argument("--model", help=f"HF model id or path (default: {DEFAULT_MODEL}; "
                                        "with --server: whatever the server has loaded)")
    parser.add_argument("--server", metavar="URL",
                        help="Use a running OpenAI-compatible server instead of loading the model "
                             "(vllm serve: http://localhost:8000, ollama: http://localhost:11434)")
    parser.add_argument("--out", type=Path, help="Rankings JSONL to write (benchmark mode)")
    parser.add_argument("--limit", type=int, help="Only the first N benchmark queries (smoke test)")
    parser.add_argument("--max-model-len", type=int, default=12288)
    parser.add_argument("--max-tokens", type=int, default=768, help="Max generated tokens per prompt")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    parser.add_argument("--all-restaurants", action="store_true",
                        help="Ad-hoc search over every restaurant in data/menus/, not just the benchmark set")
    args = parser.parse_args()
    if not args.terms and not args.out:
        parser.error("give query words for an ad-hoc search, or --out FILE to run the benchmark")

    restaurants, menus = load_data(None if args.terms and args.all_restaurants else judged_restaurant_ids())
    if args.server:
        llm = ServerLLM(args.server, model=args.model)
    else:
        llm = load_llm(args.model or DEFAULT_MODEL, args.max_model_len, args.gpu_memory_utilization)
    model_name = getattr(llm, "model", None) or args.model or DEFAULT_MODEL

    if args.terms:
        query = " ".join(args.terms)
        t0 = time.time()
        results = search(query, llm, restaurants, menus)
        print(f"\nQuery: '{query}'  ({model_name}, {time.time() - t0:.1f}s)\n")
        print_results(results, restaurants)
        sys.exit(0)

    queries = load_queries()[: args.limit] if args.limit else load_queries()
    run(queries, restaurants, menus, model_name, args.out, max_tokens=args.max_tokens, llm=llm)

    results = evaluate(replay_search_fn(args.out),
                       query_ids={q["query_id"] for q in queries})
    print_report(results)
    metrics_path = args.out.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(
        {k: results[k] for k in ("overall", "by_category", "by_difficulty")}, indent=2))
    print(f"Wrote {metrics_path}")
