#!/usr/bin/env python
"""
Run one benchmark experiment and record it under research/agent/.

An experiment is an optional setup command (train a model, generate LLM
rankings, ...) followed by research/search/evaluate.py with the given engine
arguments. Everything after `--` is passed to evaluate.py:

    python research/agent/run_experiment.py --name text-baseline -- --engine text
    python research/agent/run_experiment.py --name ce-minilm-l12 -- \\
        --engine crossencoder --model cross-encoder/ms-marco-MiniLM-L12-v2
    python research/agent/run_experiment.py --name llm-qwen2.5-7b \\
        --setup "python research/search/llm_search.py --model Qwen/Qwen2.5-7B-Instruct --out research/agent/runs/qwen.jsonl" \\
        -- --engine llm --rankings research/agent/runs/qwen.jsonl

Records (all text, committed by the campaign notebook):
- research/agent/results/<name>.json — the latest run of this experiment
  (overwritten on re-run; git history keeps older runs): status, commands,
  git commit, run time, overall / by_category / by_difficulty metrics, and
  the error tail if it failed.
- research/agent/results/history.jsonl — one line per run with the key metrics.
- research/agent/summary.csv — one row per experiment, rebuilt from results/.
- research/agent/LEADERBOARD.md — best experiment per method family, and all experiments ranked by
  efficiency = NDCG@5 / (seconds per query + 5), rebuilt from results/.
- research/agent/AGENT_NOTES.md — a short human-readable entry.

Always writes the result file (status SUCCESS / SETUP_FAILED / EVAL_FAILED)
and exits 0 unless even that fails, so callers only need to read the file.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "research" / "agent"
EVALUATE = REPO_ROOT / "research" / "search" / "evaluate.py"
METRICS = ("ndcg@5", "recall@10", "mrr")
LOG_DIR = AGENT_DIR / "runs" / "logs"   # full output of failed setup / eval commands

# Method family of each engine, so the agents improve every kind of approach, not only the current
# leader. Anything that calls an LLM (including hybrids) is "llm". New engines pass --family.
FAMILIES = {
    "text": "lexical", "enhanced": "lexical", "filtered": "lexical",
    "soft_bm25": "word-vector",
    "sbert": "bi-encoder", "colbert": "late-interaction", "crossencoder": "cross-encoder",
    "llm": "llm", "hybrid": "llm",
}
FAMILY_CHOICES = ["lexical", "word-vector", "bi-encoder", "late-interaction", "cross-encoder", "llm", "other"]

# Efficiency = NDCG@5 / (seconds per query + TIME_OFFSET). The offset keeps a method that returns bad
# results instantly from ranking first; below about a second per query it matters little.
TIME_OFFSET = 5.0


def gpu_name() -> str:
    """GPU this run used (first GPU's name from nvidia-smi), or "cpu"."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        return out.splitlines()[0].strip() if out else "cpu"
    except Exception:
        return "cpu"


def git_commit_sha() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


# Lines worth surfacing from a failed command's output: tools such as vLLM print the root cause
# well above the final traceback, which a plain tail cuts off.
_KEY_LINE = re.compile(r"(Error|Exception|error:|CUDA error|out of memory|OOM|not supported|No module named|"
                       r"Killed|Traceback|FAILED|failed)")


def summarize_failure(out: str, max_key_lines: int = 40, tail: int = 1500) -> str:
    """Key error lines from the whole output (deduplicated, in order) plus the tail."""
    keys, seen = [], set()
    for line in out.splitlines():
        s = line.strip()
        if s and _KEY_LINE.search(s) and not s.startswith("File ") and s not in seen:
            seen.add(s)
            keys.append(s[:400])
    key_text = "\n".join(keys[-max_key_lines:])
    return f"Key lines:\n{key_text}\n\n--- last {tail} chars ---\n{out[-tail:]}"


def python_shim_env() -> dict:
    """Environment whose PATH makes `python`, `python3` and `pip` in shell commands mean this interpreter.

    On Colab, `python` on PATH is a different interpreter from the notebook kernel's, with its own
    packages: a setup command like `python research/search/llm_search.py` then ran the Colab image's
    vLLM without the torchvision the notebook had installed into the kernel's interpreter."""
    shim = Path(tempfile.gettempdir()) / "agent-python-shim"
    shim.mkdir(exist_ok=True)
    for name in ("python", "python3"):
        link = shim / name
        if not (link.is_symlink() and os.readlink(link) == sys.executable):
            link.unlink(missing_ok=True)
            link.symlink_to(sys.executable)
    pip = shim / "pip"
    pip.write_text(f'#!/bin/sh\nexec "{sys.executable}" -m pip "$@"\n')
    pip.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{shim}{os.pathsep}{env.get('PATH', '')}"
    return env


def run_logged(cmd, shell: bool, timeout: float | None, log_path: Path | None = None) -> tuple[bool, str, float]:
    """(ok, output tail or failure summary, seconds). On failure the full output is written to log_path."""
    print(f"$ {cmd if shell else ' '.join(map(str, cmd))}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, shell=shell, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout,
                              env=python_shim_env())
        out = proc.stdout + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr.strip() else "")
        failed = f"Exit code {proc.returncode}" if proc.returncode != 0 else None
    except subprocess.TimeoutExpired as e:
        dec = lambda b: b.decode(errors="replace") if isinstance(b, bytes) else (b or "")
        out = dec(e.stdout) + "\n--- STDERR ---\n" + dec(e.stderr)
        failed = f"Timed out after {timeout:.0f}s"
    print(out[-3000:], flush=True)
    if not failed:
        return True, out[-3000:], time.time() - t0
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(out[-1_000_000:], encoding="utf-8")   # text, well under the notebook's 20 MB commit limit
        failed += f" (full output: {log_path.relative_to(REPO_ROOT) if log_path.is_relative_to(REPO_ROOT) else log_path})"
    return False, f"{failed}\n{summarize_failure(out)}", time.time() - t0


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "experiment"


def fmt(v):
    return round(v, 4) if isinstance(v, float) else v


def arg_value(args: list[str], flag: str) -> str | None:
    """Value of `--flag VALUE` or `--flag=VALUE` in an argument list."""
    for i, a in enumerate(args):
        if a == flag and i + 1 < len(args):
            return args[i + 1]
        if a.startswith(flag + "="):
            return a.split("=", 1)[1]
    return None


def family_of(eval_args: list[str], explicit: str | None) -> str:
    return explicit or FAMILIES.get(arg_value(eval_args, "--engine") or "text", "other")


def rankings_seconds_per_query(eval_args: list[str]) -> float:
    """Generation time per query of a --rankings file (llm_search.py records it in the meta line),
    since replaying the rankings at evaluation time takes no time."""
    path = arg_value(eval_args, "--rankings")
    if not path:
        return 0.0
    try:
        with open(REPO_ROOT / path, encoding="utf-8") as f:
            meta = json.loads(f.readline()).get("meta", {})
        return float(meta["seconds"]) / max(int(meta["n_queries"]), 1)
    except Exception:
        return 0.0


def efficiency(ndcg: float | None, sec_per_query: float | None) -> float | None:
    if ndcg is None or sec_per_query is None:
        return None
    return ndcg / (sec_per_query + TIME_OFFSET)


def write_summary(results_dir: Path, out_csv: Path) -> None:
    """summary.csv (one row per experiment, best NDCG@5 first) and LEADERBOARD.md next to it."""
    rows = []
    for p in sorted(results_dir.glob("*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        o = (r.get("metrics") or {}).get("overall") or {}
        spq = (r.get("timing") or {}).get("seconds_per_query")
        rows.append({
            "name": r.get("name"), "family": r.get("family") or family_of(r.get("eval_args") or [], None),
            "status": r.get("status"),
            **{m: fmt(o.get(m)) for m in METRICS},
            "sec_per_query": spq, "gpu": r.get("gpu"), "efficiency": fmt(efficiency(o.get("ndcg@5"), spq)),
            "n_queries": o.get("n_queries"), "seconds": r.get("seconds"),
            "git_commit": r.get("git_commit"), "timestamp": r.get("timestamp"),
            "eval_args": " ".join(r.get("eval_args") or []),
        })
    rows.sort(key=lambda r: -(r["ndcg@5"] or -1))
    fields = ["name", "family", "status", *METRICS, "sec_per_query", "gpu", "efficiency", "n_queries", "seconds",
              "git_commit", "timestamp", "eval_args"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    write_leaderboard([r for r in rows if r["status"] == "SUCCESS"], out_csv.parent / "LEADERBOARD.md")


def write_leaderboard(rows: list[dict], path: Path) -> None:
    def cell(v):
        return "–" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))
    lines = ["# Leaderboard", "",
             "Rebuilt by `run_experiment.py` from `results/`. Seconds per query include LLM generation for",
             "engines that replay `--rankings`, and depend on the GPU (column GPU): compare them only between",
             "runs on the same GPU. `–` = not recorded (re-run it).", "",
             "## Best per method family (by NDCG@5)", "",
             "| Family | Best experiment | NDCG@5 | Recall@10 | MRR | s/query | GPU | Efficiency | Experiments |",
             "|---|---|---|---|---|---|---|---|---|"]
    for fam in FAMILY_CHOICES:
        fr = [r for r in rows if r["family"] == fam]
        if not fr:
            lines.append(f"| {fam} | (none yet) | | | | | | | 0 |")
            continue
        b = max(fr, key=lambda r: r["ndcg@5"] or -1)
        lines.append(f"| {fam} | {b['name']} | {cell(b['ndcg@5'])} | {cell(b['recall@10'])} | {cell(b['mrr'])} "
                     f"| {cell(b['sec_per_query'])} | {cell(b['gpu'])} | {cell(b['efficiency'])} | {len(fr)} |")
    lines += ["", f"## Efficiency = NDCG@5 / (seconds per query + {TIME_OFFSET:g})", "",
              "| # | Experiment | Family | Efficiency | NDCG@5 | s/query | GPU |", "|---|---|---|---|---|---|---|"]
    ranked = sorted(rows, key=lambda r: -(r["efficiency"] if r["efficiency"] is not None else -1))
    for i, r in enumerate(ranked, 1):
        lines.append(f"| {i} | {r['name']} | {r['family']} | {cell(r['efficiency'])} | {cell(r['ndcg@5'])} "
                     f"| {cell(r['sec_per_query'])} | {cell(r['gpu'])} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_notes(notes_file: Path, row: dict) -> None:
    head = f"\n### Iteration {row['iteration']}: {row['name']}" if row.get("iteration") is not None \
        else f"\n### {row['name']}"
    lines = [f"{head} ({row['status']})",
             f"- Result: `{row['result_file']}` | commit `{row.get('git_commit')}` | {row.get('seconds')}s"]
    if row.get("setup"):
        lines.append(f"- Setup: `{row['setup']}`")
    lines.append(f"- Eval args: `{' '.join(row['eval_args'])}` | family `{row['family']}`")
    if row["status"] == "SUCCESS":
        o = row["metrics"]["overall"]
        spq = row["timing"]["seconds_per_query"]
        lines.append("- " + " | ".join(f"{m} {fmt(o.get(m))}" for m in METRICS)
                     + f" | {spq} s/query on {row.get('gpu')} | efficiency {fmt(efficiency(o.get('ndcg@5'), spq))}"
                     + f" | {o.get('n_with_judgments')}/{o.get('n_queries')} queries judged")
        cats = sorted(row["metrics"].get("by_category", {}).items(), key=lambda kv: kv[1].get("ndcg@5", 0))
        lines.append("- Weakest categories (NDCG@5): " + ", ".join(
            f"{cid} {v.get('name', '')} {fmt(v.get('ndcg@5'))}" for cid, v in cats[:5]))
    else:
        lines.append(f"- Error:\n```\n{(row.get('error') or '')[:1500]}\n```")
    notes_file.parent.mkdir(parents=True, exist_ok=True)
    with open(notes_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    argv = sys.argv[1:]
    eval_args = argv[argv.index("--") + 1:] if "--" in argv else []
    own = argv[:argv.index("--")] if "--" in argv else argv

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                     usage="%(prog)s --name NAME [--setup CMD] -- EVALUATE_ARGS...")
    parser.add_argument("--name", required=True, help="Experiment name; result file is results/<name>.json")
    parser.add_argument("--setup", help="Shell command run from the repo root before evaluation "
                                        "(training, generating LLM rankings, ...)")
    parser.add_argument("--description", default="", help="One line on what this experiment tests")
    parser.add_argument("--family", choices=FAMILY_CHOICES,
                        help="Method family; default from the engine (anything using an LLM is 'llm')")
    parser.add_argument("--iteration", type=int, help="Campaign iteration number, for the notes")
    parser.add_argument("--setup-timeout", type=float, default=None, help="Seconds; default no limit")
    parser.add_argument("--eval-timeout", type=float, default=None, help="Seconds; default no limit")
    parser.add_argument("--results-dir", type=Path, default=AGENT_DIR / "results")
    parser.add_argument("--notes-file", default=str(AGENT_DIR / "AGENT_NOTES.md"),
                        help="Markdown notes to append to; pass '' to skip")
    args = parser.parse_args(own)
    if not eval_args:
        parser.error("give evaluate.py arguments after `--`, e.g. -- --engine text")

    name = safe_name(args.name)
    args.results_dir = args.results_dir.resolve()
    result_file = args.results_dir / f"{name}.json"
    try:
        result_rel = str(result_file.relative_to(REPO_ROOT))
    except ValueError:      # results dir outside the repo (testing)
        result_rel = str(result_file)
    row = {
        "name": name, "description": args.description, "status": "SUCCESS",
        "iteration": args.iteration, "timestamp": datetime.now().isoformat(timespec="seconds"),
        "git_commit": git_commit_sha(), "gpu": gpu_name(), "result_file": result_rel,
        "family": family_of(eval_args, args.family),
        "setup": args.setup, "eval_args": eval_args, "seconds": None, "timing": None, "metrics": None,
    }
    t0 = time.time()
    try:
        if args.setup:
            ok, out, secs = run_logged(args.setup, shell=True, timeout=args.setup_timeout,
                                         log_path=LOG_DIR / f"{name}.setup.log")
            row["setup_seconds"] = round(secs, 1)
            if not ok:
                row.update(status="SETUP_FAILED", error=out)
        if row["status"] == "SUCCESS":
            with tempfile.TemporaryDirectory() as tmp:
                metrics_path = Path(tmp) / "metrics.json"
                cmd = [sys.executable, str(EVALUATE), *eval_args, "--save-metrics", str(metrics_path)]
                ok, out, secs = run_logged(cmd, shell=False, timeout=args.eval_timeout,
                                             log_path=LOG_DIR / f"{name}.eval.log")
                row["eval_seconds"] = round(secs, 1)
                if ok and metrics_path.exists():
                    m = json.loads(metrics_path.read_text())
                    row["metrics"] = {k: m[k] for k in ("overall", "by_category", "by_difficulty")}
                    gen = rankings_seconds_per_query(eval_args)
                    search = (m.get("timing") or {}).get("seconds_per_query", 0.0)
                    row["timing"] = {"seconds_per_query": round(search + gen, 4),
                                     "search_seconds_per_query": search,
                                     "rankings_generation_seconds_per_query": round(gen, 4)}
                else:
                    row.update(status="EVAL_FAILED", error=out if not ok else "evaluate.py wrote no metrics")
    except Exception:
        import traceback
        row.update(status="EVAL_FAILED", error=traceback.format_exc())
    row["seconds"] = round(time.time() - t0, 1)

    args.results_dir.mkdir(parents=True, exist_ok=True)
    result_file.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    print(f"Result ({row['status']}) written to {result_file}")

    o = (row["metrics"] or {}).get("overall", {})
    with open(args.results_dir / "history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({k: row.get(k) for k in ("timestamp", "iteration", "git_commit", "gpu", "name", "family",
                                                     "status", "setup", "eval_args", "seconds")}
                           | {"metrics": {m: fmt(o.get(m)) for m in METRICS} if o else None,
                              "seconds_per_query": (row.get("timing") or {}).get("seconds_per_query")}) + "\n")
    write_summary(args.results_dir, args.results_dir.parent / "summary.csv")
    if args.notes_file:
        write_notes(Path(args.notes_file), row)


if __name__ == "__main__":
    main()
