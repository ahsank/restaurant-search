# Agent notes

Appended by `research/colab/agent_campaign.ipynb` and `run_experiment.py`:
one entry per experiment, plan and code change. The first tasks re-run the existing engines on the
current labels, so the agent starts from comparable baselines.

### Iteration 0: baseline-text (SUCCESS)
- Result: `research/agent/results/baseline-text.json` | commit `2646904` | 0.1s
- Eval args: `--engine text`
- ndcg@5 0.4456 | recall@10 0.4708 | mrr 0.4692 | 206/209 queries judged
- Weakest categories (NDCG@5): C01 Cuisine type inference 0.0, C02 Ingredient generalization 0.0, C08 Dietary constraint / negation 0.0, C10 Multi-constraint compositional 0.0, C25 Occasion / meal-time 0.0

### Iteration 1: baseline-enhanced (SUCCESS)
- Result: `research/agent/results/baseline-enhanced.json` | commit `7e6ec25` | 2.2s
- Eval args: `--engine enhanced`
- ndcg@5 0.5484 | recall@10 0.5498 | mrr 0.5925 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C02 Ingredient generalization 0.0553, C05 Spelling variations 0.0667, C03 Attribute / implied meaning 0.1224, C08 Dietary constraint / negation 0.1987

### Iteration 2: sbert-all-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/sbert-all-MiniLM-L6-v2.json` | commit `7d057b3` | 20.7s
- Eval args: `--engine sbert --model all-MiniLM-L6-v2`
- ndcg@5 0.5592 | recall@10 0.4883 | mrr 0.7093 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C18 Chicken dishes 0.1969, C03 Attribute / implied meaning 0.2386, C04 Cooking method synonyms 0.3205, C02 Ingredient generalization 0.3335

### Iteration 3: sbert-all-mpnet-base-v2 (SUCCESS)
- Result: `research/agent/results/sbert-all-mpnet-base-v2.json` | commit `f51b5b3` | 11.2s
- Eval args: `--engine sbert --model all-mpnet-base-v2`
- ndcg@5 0.5577 | recall@10 0.4803 | mrr 0.7158 | 206/209 queries judged
- Weakest categories (NDCG@5): C03 Attribute / implied meaning 0.1655, C10 Multi-constraint compositional 0.1689, C08 Dietary constraint / negation 0.2537, C18 Chicken dishes 0.2967, C02 Ingredient generalization 0.3423

### Iteration 4: colbert-colbertv2.0 (SUCCESS)
- Result: `research/agent/results/colbert-colbertv2.0.json` | commit `ef1f595` | 11.8s
- Eval args: `--engine colbert`
- ndcg@5 0.6422 | recall@10 0.5616 | mrr 0.7851 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0976, C03 Attribute / implied meaning 0.2194, C25 Occasion / meal-time 0.2965, C08 Dietary constraint / negation 0.331, C02 Ingredient generalization 0.386

### Iteration 5: crossencoder-ms-marco-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/crossencoder-ms-marco-MiniLM-L6-v2.json` | commit `ae01ce2` | 20.2s
- Eval args: `--engine crossencoder --model cross-encoder/ms-marco-MiniLM-L6-v2`
- ndcg@5 0.651 | recall@10 0.5874 | mrr 0.7989 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C25 Occasion / meal-time 0.2648, C03 Attribute / implied meaning 0.2755, C08 Dietary constraint / negation 0.3316, C02 Ingredient generalization 0.4157
