# Agent notes

Appended by `research/colab/agent_campaign.ipynb` and `run_experiment.py`:
one entry per experiment, plan and code change. The first tasks re-run the existing engines on the
current labels, so the agent starts from comparable baselines.

### Iteration 0: baseline-text (SUCCESS)
- Result: `research/agent/results/baseline-text.json` | commit `2646904` | 0.1s
- Eval args: `--engine text`
- ndcg@5 0.4456 | recall@10 0.4708 | mrr 0.4692 | 206/209 queries judged
- Weakest categories (NDCG@5): C01 Cuisine type inference 0.0, C02 Ingredient generalization 0.0, C08 Dietary constraint / negation 0.0, C10 Multi-constraint compositional 0.0, C25 Occasion / meal-time 0.0
