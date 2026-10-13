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


def git_commit_sha() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def run_logged(cmd, shell: bool, timeout: float | None) -> tuple[bool, str, float]:
    """(ok, combined output tail, seconds). Output is streamed to stdout as well."""
    print(f"$ {cmd if shell else ' '.join(map(str, cmd))}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, shell=shell, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return False, f"Timed out after {timeout:.0f}s\n{out[-2000:]}", time.time() - t0
    out = proc.stdout + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr.strip() else "")
    print(proc.stdout[-3000:], flush=True)
    if proc.returncode != 0:
        return False, f"Exit code {proc.returncode}\n{out[-3000:]}", time.time() - t0
    return True, out[-3000:], time.time() - t0


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "experiment"


def fmt(v):
    return round(v, 4) if isinstance(v, float) else v


def write_summary(results_dir: Path, out_csv: Path) -> None:
    """One row per experiment (latest run), best NDCG@5 first."""
    rows = []
    for p in sorted(results_dir.glob("*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        o = (r.get("metrics") or {}).get("overall") or {}
        rows.append({
            "name": r.get("name"), "status": r.get("status"),
            **{m: fmt(o.get(m)) for m in METRICS},
            "n_queries": o.get("n_queries"), "seconds": r.get("seconds"),
            "git_commit": r.get("git_commit"), "timestamp": r.get("timestamp"),
            "eval_args": " ".join(r.get("eval_args") or []),
        })
    rows.sort(key=lambda r: -(r["ndcg@5"] or -1))
    fields = ["name", "status", *METRICS, "n_queries", "seconds", "git_commit", "timestamp", "eval_args"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_notes(notes_file: Path, row: dict) -> None:
    head = f"\n### Iteration {row['iteration']}: {row['name']}" if row.get("iteration") is not None \
        else f"\n### {row['name']}"
    lines = [f"{head} ({row['status']})",
             f"- Result: `{row['result_file']}` | commit `{row.get('git_commit')}` | {row.get('seconds')}s"]
    if row.get("setup"):
        lines.append(f"- Setup: `{row['setup']}`")
    lines.append(f"- Eval args: `{' '.join(row['eval_args'])}`")
    if row["status"] == "SUCCESS":
        o = row["metrics"]["overall"]
        lines.append("- " + " | ".join(f"{m} {fmt(o.get(m))}" for m in METRICS)
                     + f" | {o.get('n_with_judgments')}/{o.get('n_queries')} queries judged")
        cats = sorted(row["metrics"].get("by_category", {}).items(), key=lambda kv: kv[1].get("ndcg@5", 0))
        lines.append("- Weakest categories (NDCG@5): " + ", ".join(
            f"{cid} {v.get('name', '')} {fmt(v.get('ndcg@5'))}" for cid, v in cats[:5]))
    else:
        lines.append(f"- Error:\n```\n{(row.get('error') or '')[-800:]}\n```")
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
        "git_commit": git_commit_sha(), "result_file": result_rel,
        "setup": args.setup, "eval_args": eval_args, "seconds": None, "metrics": None,
    }
    t0 = time.time()
    try:
        if args.setup:
            ok, out, secs = run_logged(args.setup, shell=True, timeout=args.setup_timeout)
            row["setup_seconds"] = round(secs, 1)
            if not ok:
                row.update(status="SETUP_FAILED", error=out)
        if row["status"] == "SUCCESS":
            with tempfile.TemporaryDirectory() as tmp:
                metrics_path = Path(tmp) / "metrics.json"
                cmd = [sys.executable, str(EVALUATE), *eval_args, "--save-metrics", str(metrics_path)]
                ok, out, secs = run_logged(cmd, shell=False, timeout=args.eval_timeout)
                row["eval_seconds"] = round(secs, 1)
                if ok and metrics_path.exists():
                    m = json.loads(metrics_path.read_text())
                    row["metrics"] = {k: m[k] for k in ("overall", "by_category", "by_difficulty")}
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
        f.write(json.dumps({k: row.get(k) for k in ("timestamp", "iteration", "git_commit", "name", "status",
                                                     "setup", "eval_args", "seconds")}
                           | {"metrics": {m: fmt(o.get(m)) for m in METRICS} if o else None}) + "\n")
    write_summary(args.results_dir, args.results_dir.parent / "summary.csv")
    if args.notes_file:
        write_notes(Path(args.notes_file), row)


if __name__ == "__main__":
    main()
