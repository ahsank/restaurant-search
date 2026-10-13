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

### Iteration 6: llm-qwen2.5-7b-instruct (SUCCESS)
- Result: `research/agent/results/llm-qwen2.5-7b-instruct.json` | commit `2cb8536` | 232.4s
- Setup: `python research/search/llm_search.py --model Qwen/Qwen2.5-7B-Instruct --out research/agent/runs/qwen2.5-7b-instruct.jsonl --gpu-memory-utilization 0.85`
- Eval args: `--engine llm --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl`
- ndcg@5 0.6993 | recall@10 0.7739 | mrr 0.7687 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2461, C03 Attribute / implied meaning 0.435, C18 Chicken dishes 0.484, C02 Ingredient generalization 0.5651, C25 Occasion / meal-time 0.5996

### Plan (iteration 7)
- Hypothesis: While Qwen2.5-7B achieved the highest Recall@10 (0.7739) and NDCG@5 (0.6993), its coarse discrete grading and failure on empty queries held back MRR compared to ms-marco-MiniLM-L6-v2 (0.7989). First, we evaluate the deeper 12-layer cross-encoder checkpoint (ms-marco-MiniLM-L12-v2) to test if increased model capacity improves dense cross-attention ranking. Second, we implement a hybrid reranker combining LLM candidate recall with cross-encoder scoring and fallback, addressing the coarse ranking and empty-result failure modes documented in APPROACHES.md.
- Queued: run_experiment crossencoder-ms-marco-MiniLM-L12-v2
- Queued: change_code Implement a hybrid search engine in research/search/hybrid_search.py and register --engine hybrid in research/search/engines.py. The hybrid engine tak

### Iteration 7: crossencoder-ms-marco-MiniLM-L12-v2 (SUCCESS)
- Result: `research/agent/results/crossencoder-ms-marco-MiniLM-L12-v2.json` | commit `843d0da` | 27.0s
- Eval args: `--engine crossencoder --model cross-encoder/ms-marco-MiniLM-L12-v2`
- ndcg@5 0.6462 | recall@10 0.5811 | mrr 0.7869 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C25 Occasion / meal-time 0.2574, C03 Attribute / implied meaning 0.2613, C08 Dietary constraint / negation 0.304, C02 Ingredient generalization 0.3814

### Iteration 8: hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2.json` | commit `71d7fcd` | 8.4s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2`
- ndcg@5 0.784 | recall@10 0.8104 | mrr 0.8577 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0984, C08 Dietary constraint / negation 0.3233, C09 Synonym / paraphrase 0.5957, C03 Attribute / implied meaning 0.6124, C25 Occasion / meal-time 0.6262

### Iteration 8: hybrid-qwen2.5-7b-minilm-l6-boost2 (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-minilm-l6-boost2.json` | commit `71d7fcd` | 8.5s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2 --grade-boost 2.0`
- ndcg@5 0.8006 | recall@10 0.8265 | mrr 0.8707 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.1666, C08 Dietary constraint / negation 0.4846, C03 Attribute / implied meaning 0.6042, C09 Synonym / paraphrase 0.6588, C24 Pizza varieties 0.6667

### Iteration 8: code change
**Goal**: Implement a hybrid search engine in research/search/hybrid_search.py and register --engine hybrid in research/search/engines.py. The hybrid engine takes LLM candidate rankings (--rankings) and rescores them with a CrossEncoder (--model), using the cross-encoder score (optionally with an LLM grade boost) to produce fine-grained ordering, and falls back to full cross-encoder search when the LLM returns no matches. Verify with evaluate.py --engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2.

**Summary**: Implemented the hybrid search engine in research/search/hybrid_search.py and registered `--engine hybrid` in research/search/engines.py, documented usage in research/COMMANDS.md. The hybrid search engine takes LLM candidate rankings (--rankings), rescores candidates using CrossEncoder (--model, default ms-marco-MiniLM-L6-v2) with an optional grade boost (--grade-boost), and falls back to exhaustive cross-encoder search when the LLM returns no candidate matches. Benchmark results for `hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2`: NDCG@5=0.7840, Recall@10=0.8104, MRR=0.8577 (outperforming both Qwen2.5-7B's 0.6993 NDCG@5 and stock CrossEncoder's 0.6510 NDCG@5). With `--grade-boost 2.0`, performance reached NDCG@5=0.8006, Recall@10=0.8265, MRR=0.8707.

**Files changed**:
```
 M research/COMMANDS.md
 M research/search/engines.py
?? research/search/hybrid_search.py
```
