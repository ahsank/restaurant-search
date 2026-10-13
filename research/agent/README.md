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
| `summary.csv` | `run_experiment.py` | One row per experiment, best NDCG@5 first |
| `HUMAN_ACTIONS.md` | agents ([`agent_requests.py`](agent_requests.py)) | Requests for you; mark `[x]` done or `[-]` rejected, optionally add `Reply: ...` |
| `runs/` | experiments | Text outputs worth keeping, e.g. LLM rankings JSONL (replayable with `--engine llm --rankings`) |
| `setup_machine.sh` | agents | Idempotent pip installs and downloads that experiments need; the notebook runs it at the start of every session |

## Large artifacts are reproduced, not committed

Model weights, checkpoints, datasets and vector files go to `/content/scratch` or `models/` and are
never committed. An experiment that needs them must be reproducible on a fresh machine: packages and
downloads go in `setup_machine.sh` (with a line here on what each download is for), and a trained
model comes from its training script via the experiment's `setup` command. As a safety net, the
notebook leaves any file over 20 MB out of the commit and lists it in `AGENT_NOTES.md` (GitHub rejects
files over 100 MB, which would block every later push).

Downloads added by the agents:

- (none yet)

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
