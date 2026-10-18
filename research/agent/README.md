# Agent campaign

An autonomous improve/benchmark loop driven by Gemini agents in
[`research/colab/agent_campaign.ipynb`](../colab/agent_campaign.ipynb). It runs on a Colab GPU and
commits every step to the **`agent/campaign`** branch only; nothing reaches `main` until a human
reviews and merges it.

## How it works

1. When the task queue (`AGENT_TODO.json`) is empty, a **planner** agent (read-only repo tools) reads
   the results here and queues the next two tasks.
2. `run_experiment` tasks run [`run_experiment.py`](run_experiment.py): an optional setup command
   (training, generating LLM rankings, ...) and then `research/search/evaluate.py` with the given
   engine arguments.
3. `change_code` tasks run a **code agent** that can read/write repo files, install packages,
   download models (`run_shell`) and run experiments (`run_experiment`) to check its change. It names
   the experiments its change affects, and those are re-run.
4. After every task the notebook commits everything and pushes to `agent/campaign`.

**Session budget.** The time limit is checked only before calling the planner. Once a plan is made,
its tasks (and the re-runs a code change asks for) always finish, even past the budget, so new code is
evaluated in the session that wrote it rather than left for the next session's planner to build on.

**Open the notebook fresh each session** from the badge on GitHub (`agent/campaign` branch). An old
Colab tab still has the old code, and saving it would overwrite newer changes; the notebook checks its
`NOTEBOOK_VERSION` against the branch copy and refuses to run if it is older.

The planner and code agent are told: don't modify `data/` or the metric code, don't train on or
hard-code anything from the benchmark queries, labels or menu items, use `run_shell` only for
installing packages and downloading models, don't commit large artifacts (add setup steps to
`setup_machine.sh` instead), and add a request to `HUMAN_ACTIONS.md` when the evaluation or a label
looks wrong. Apart from the 20 MB file limit below, these are prompt rules, not enforced; the review
checklist below is how to catch a violation.

## Files

| File | Written by | Contents |
|---|---|---|
| `AGENT_TODO.json` | notebook | `pending_tasks`, `completed_tasks`, `iteration` |
| `AGENT_NOTES.md` | notebook, `run_experiment.py` | Plans (hypotheses), experiment results, code-change summaries with the changed files |
| `results/<name>.json` | `run_experiment.py` | Latest run of one experiment: `status` (SUCCESS / SETUP_FAILED / EVAL_FAILED), `setup`, `eval_args`, `git_commit`, `seconds`, and `metrics` with `overall`, `by_category`, `by_difficulty` (same layout as `evaluate.py --save-metrics`); `error` when it failed |
| `results/history.jsonl` | `run_experiment.py` | One line per run with key metrics, so overwritten results stay visible |
| `summary.csv` | `run_experiment.py` | One row per experiment, best NDCG@5 first, with family, seconds per query and efficiency |
| `LEADERBOARD.md` | `run_experiment.py` | Best experiment per method family, and all experiments ranked by efficiency (below) |
| `HUMAN_ACTIONS.md` | agents ([`agent_requests.py`](agent_requests.py)) | Requests for you; mark `[x]` done or `[-]` rejected, optionally add `Reply: ...` |
| `runs/` | experiments | Text outputs worth keeping, e.g. LLM rankings JSONL (replayable with `--engine llm --rankings`) |
| `setup_machine.sh` | agents | Idempotent pip installs and downloads that experiments need; the notebook runs it at the start of every session |

## Method families and efficiency

So the agents don't only polish the current leader, every experiment has a **family**: `lexical`,
`word-vector`, `bi-encoder`, `late-interaction`, `cross-encoder`, `llm` (anything that calls an LLM,
including hybrids that use LLM rankings) or `other`. It comes from the engine (`FAMILIES` in
`run_experiment.py`); a new engine passes `--family`. The planner must give every task a family and
put at least one of its two tasks per plan into a non-LLM family, rotating between them.

`evaluate.py` times the search calls (model loading and indexing excluded) and `run_experiment.py`
adds the per-query LLM generation time recorded in a `--rankings` file, so replayed LLM engines aren't
counted as free. **Efficiency** = NDCG@5 / (seconds per query + 5); the 5 s offset keeps a method that
returns bad results instantly from ranking first. Timings are from the Colab GPU, where the LLM reader
takes ~0.2 s/query, so efficiency barely penalizes it there; the per-family rule is what keeps the
non-LLM families moving.

## GPU-aware planning

The notebook detects the GPU at the start of each session (`GPU_TIER` in the install cell: `large`
≥ 40 GB such as G4/A100, `medium` such as L4, `small` such as T4, or `cpu`) and gives both agents the
matching rules. A large-GPU session is spent on work that needs it (LLM rankings, comparing LLMs,
fine-tuning); CPU-only work such as keyword-search changes is left for cheaper sessions. A small-GPU
session doesn't generate LLM rankings above ~3B (Qwen2.5-7B doesn't fit a T4) but can replay existing
rankings. Each result records its GPU, and timings are compared only between runs on the same GPU.

## Large artifacts are reproduced, not committed

Model weights, checkpoints, datasets and vector files go to `/content/scratch` or `models/` and are
never committed. An experiment that needs them must be reproducible on a fresh machine: packages and
downloads go in `setup_machine.sh` (with a line here on what each download is for), and a trained
model comes from its training script via the experiment's `setup` command. As a safety net, the
notebook leaves any file over 20 MB out of the commit and lists it in `AGENT_NOTES.md` (GitHub rejects
files over 100 MB, which would block every later push).

Downloads added by the agents:

- `numberbatch-en-19.08.txt.gz`: ConceptNet Numberbatch 19.08 English embeddings (~75 MB compressed, ~300 MB uncompressed) for Phrase-Aware Soft-BM25 search (`--engine soft_bm25 --vectors ...`).

## Running an experiment by hand

```bash
python research/agent/run_experiment.py --name baseline-text -- --engine text
python research/agent/run_experiment.py --name ce-minilm-l12 -- \
    --engine crossencoder --model cross-encoder/ms-marco-MiniLM-L12-v2
python research/agent/run_experiment.py --name llm-qwen2.5-7b-instruct \
    --setup "python research/search/llm_search.py --model Qwen/Qwen2.5-7B-Instruct --out research/agent/runs/qwen2.5-7b-instruct.jsonl" \
    -- --engine llm --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl
```

## Reviewing the branch before merging

- `git log --stat main..agent/campaign` and `AGENT_NOTES.md` for what was tried and why.
- `git diff main...agent/campaign -- data/ research/search/evaluate.py research/lib/` should be
  empty: the benchmark and metrics are off-limits.
- New training code or prompts must not use the benchmark: search the diff for `relevance_`,
  `queries.csv` or `data/menus` outside search-time loading, and for dish names copied from the
  menus into prompts, synonym lists or training data.
- Re-run a claimed result yourself with the `setup` / `eval_args` stored in its result file.
- Answer `HUMAN_ACTIONS.md`.

Merge what's worth keeping (or cherry-pick), not necessarily the whole branch.
