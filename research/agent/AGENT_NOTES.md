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

### Plan (iteration 9)
- Hypothesis: Hybrid Qwen2.5-7B with ms-marco-MiniLM-L6-v2 and grade-boost 2.0 set a new benchmark high (NDCG@5=0.8006, Recall@10=0.8265, MRR=0.8707), but category analysis shows C08 (Dietary constraint) dropped from 0.6651 under Qwen to 0.4846 under hybrid. This regression is caused by two factors: `hybrid_search.py` omits dietary metadata from the passage text passed to CrossEncoder, and raw CrossEncoder logit swings occasionally override high-confidence LLM grade 2 judgments. We first evaluate the deeper 12-layer CrossEncoder (MiniLM-L12-v2) on the existing hybrid setup, then update `hybrid_search.py` to include dietary annotations in candidate passage text and support strict-grade tiering.
- Queued: run_experiment hybrid-qwen2.5-7b-minilm-l12-boost2
- Queued: change_code Update research/search/hybrid_search.py to include item['dietary'] in the candidate text passed to CrossEncoder, and add a --strict-grade flag (rankin

### Iteration 9: hybrid-qwen2.5-7b-minilm-l12-boost2 (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-minilm-l12-boost2.json` | commit `55fe4aa` | 9.4s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L12-v2 --grade-boost 2.0`
- ndcg@5 0.7999 | recall@10 0.8246 | mrr 0.8611 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.1365, C08 Dietary constraint / negation 0.4595, C03 Attribute / implied meaning 0.5384, C09 Synonym / paraphrase 0.6583, C24 Pizza varieties 0.6667

### Iteration 10: hybrid-qwen2.5-7b-minilm-l6-strict-grade (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-minilm-l6-strict-grade.json` | commit `b478545` | 8.5s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2 --strict-grade`
- ndcg@5 0.7858 | recall@10 0.821 | mrr 0.8665 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2461, C03 Attribute / implied meaning 0.5606, C18 Chicken dishes 0.6401, C09 Synonym / paraphrase 0.6662, C24 Pizza varieties 0.6667

### Iteration 10: code change
**Goal**: Update research/search/hybrid_search.py to include item['dietary'] in the candidate text passed to CrossEncoder, and add a --strict-grade flag (ranking items by grade first, and breaking intra-grade ties by CrossEncoder score). Verify by evaluating on evaluate.py --engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2 --strict-grade.

**Summary**: Updated research/search/hybrid_search.py to include item['dietary'] in candidate text passed to CrossEncoder and added candidate_item_text helper to index dietary annotations across candidate items and fallback search. Added --strict-grade flag to rank items strictly by LLM grade first (2 before 1) and break intra-grade ties by CrossEncoder score. Updated research/search/engines.py to forward --strict-grade to hybrid search and documented the flag in research/COMMANDS.md. Evaluated hybrid search with ms-marco-MiniLM-L6-v2 and --strict-grade: overall NDCG@5=0.7858, Recall@10=0.8210, MRR=0.8665, with C08 (Dietary constraint / negation) improving significantly from 0.4846 to 0.7193 NDCG@5 and MRR from 0.7012 to 0.8148.

**Files changed**:
```
 M research/COMMANDS.md
 M research/search/engines.py
 M research/search/hybrid_search.py
```

### Iteration 11: baseline-enhanced (SUCCESS)
- Result: `research/agent/results/baseline-enhanced.json` | commit `9afa8a0` | 2.2s
- Eval args: `--engine enhanced` | family `lexical`
- ndcg@5 0.5484 | recall@10 0.5498 | mrr 0.5925 | 0.0103 s/query | efficiency 0.1095 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C02 Ingredient generalization 0.0553, C05 Spelling variations 0.0667, C03 Attribute / implied meaning 0.1224, C08 Dietary constraint / negation 0.1987

### Iteration 12: baseline-text (SUCCESS)
- Result: `research/agent/results/baseline-text.json` | commit `4d21690` | 0.1s
- Eval args: `--engine text` | family `lexical`
- ndcg@5 0.4456 | recall@10 0.4708 | mrr 0.4692 | 0.0003 s/query | efficiency 0.0891 | 206/209 queries judged
- Weakest categories (NDCG@5): C01 Cuisine type inference 0.0, C02 Ingredient generalization 0.0, C08 Dietary constraint / negation 0.0, C10 Multi-constraint compositional 0.0, C25 Occasion / meal-time 0.0

### Iteration 13: colbert-colbertv2.0 (SUCCESS)
- Result: `research/agent/results/colbert-colbertv2.0.json` | commit `cfb208c` | 25.4s
- Eval args: `--engine colbert` | family `late-interaction`
- ndcg@5 0.6422 | recall@10 0.5616 | mrr 0.7851 | 0.0095 s/query | efficiency 0.1282 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0976, C03 Attribute / implied meaning 0.2194, C25 Occasion / meal-time 0.2965, C08 Dietary constraint / negation 0.331, C02 Ingredient generalization 0.386

### Iteration 14: crossencoder-ms-marco-MiniLM-L12-v2 (SUCCESS)
- Result: `research/agent/results/crossencoder-ms-marco-MiniLM-L12-v2.json` | commit `b90cdb0` | 26.8s
- Eval args: `--engine crossencoder --model cross-encoder/ms-marco-MiniLM-L12-v2` | family `cross-encoder`
- ndcg@5 0.6462 | recall@10 0.5811 | mrr 0.7869 | 0.0872 s/query | efficiency 0.127 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C25 Occasion / meal-time 0.2574, C03 Attribute / implied meaning 0.2613, C08 Dietary constraint / negation 0.304, C02 Ingredient generalization 0.3814

### Iteration 15: crossencoder-ms-marco-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/crossencoder-ms-marco-MiniLM-L6-v2.json` | commit `458e855` | 20.0s
- Eval args: `--engine crossencoder --model cross-encoder/ms-marco-MiniLM-L6-v2` | family `cross-encoder`
- ndcg@5 0.651 | recall@10 0.5874 | mrr 0.7989 | 0.0549 s/query | efficiency 0.1288 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C25 Occasion / meal-time 0.2648, C03 Attribute / implied meaning 0.2755, C08 Dietary constraint / negation 0.3316, C02 Ingredient generalization 0.4157

### Iteration 16: hybrid-qwen2.5-7b-minilm-l12-boost2 (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-minilm-l12-boost2.json` | commit `4c87ac0` | 9.2s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L12-v2 --grade-boost 2.0` | family `llm`
- ndcg@5 0.8058 | recall@10 0.8273 | mrr 0.8637 | 0.2022 s/query | efficiency 0.1549 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.259, C08 Dietary constraint / negation 0.5356, C03 Attribute / implied meaning 0.5479, C09 Synonym / paraphrase 0.6583, C24 Pizza varieties 0.6667

### Iteration 17: hybrid-qwen2.5-7b-minilm-l6-boost2 (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-minilm-l6-boost2.json` | commit `130b6e2` | 8.5s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2 --grade-boost 2.0` | family `llm`
- ndcg@5 0.8013 | recall@10 0.8299 | mrr 0.867 | 0.1987 s/query | efficiency 0.1541 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2461, C08 Dietary constraint / negation 0.5659, C03 Attribute / implied meaning 0.5668, C09 Synonym / paraphrase 0.6588, C24 Pizza varieties 0.6667

### Iteration 18: hybrid-qwen2.5-7b-minilm-l6-strict-grade (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-minilm-l6-strict-grade.json` | commit `ed60ce2` | 8.5s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2 --strict-grade` | family `llm`
- ndcg@5 0.7858 | recall@10 0.821 | mrr 0.8665 | 0.1987 s/query | efficiency 0.1512 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2461, C03 Attribute / implied meaning 0.5606, C18 Chicken dishes 0.6401, C09 Synonym / paraphrase 0.6662, C24 Pizza varieties 0.6667

### Iteration 19: hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2.json` | commit `0d7f654` | 8.5s
- Eval args: `--engine hybrid --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl --model cross-encoder/ms-marco-MiniLM-L6-v2` | family `llm`
- ndcg@5 0.7909 | recall@10 0.8146 | mrr 0.8578 | 0.1987 s/query | efficiency 0.1521 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2461, C08 Dietary constraint / negation 0.4692, C03 Attribute / implied meaning 0.5902, C09 Synonym / paraphrase 0.5957, C02 Ingredient generalization 0.6526

### Iteration 20: llm-qwen2.5-7b-instruct (SUCCESS)
- Result: `research/agent/results/llm-qwen2.5-7b-instruct.json` | commit `085e267` | 0.1s
- Eval args: `--engine llm --rankings research/agent/runs/qwen2.5-7b-instruct.jsonl` | family `llm`
- ndcg@5 0.6993 | recall@10 0.7739 | mrr 0.7687 | 0.1914 s/query | efficiency 0.1347 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2461, C03 Attribute / implied meaning 0.435, C18 Chicken dishes 0.484, C02 Ingredient generalization 0.5651, C25 Occasion / meal-time 0.5996

### Iteration 21: sbert-all-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/sbert-all-MiniLM-L6-v2.json` | commit `03cd080` | 9.7s
- Eval args: `--engine sbert --model all-MiniLM-L6-v2` | family `bi-encoder`
- ndcg@5 0.5592 | recall@10 0.4883 | mrr 0.7093 | 0.0032 s/query | efficiency 0.1118 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C18 Chicken dishes 0.1969, C03 Attribute / implied meaning 0.2386, C04 Cooking method synonyms 0.3205, C02 Ingredient generalization 0.3335

### Iteration 22: sbert-all-mpnet-base-v2 (SUCCESS)
- Result: `research/agent/results/sbert-all-mpnet-base-v2.json` | commit `f4ca7e8` | 10.9s
- Eval args: `--engine sbert --model all-mpnet-base-v2` | family `bi-encoder`
- ndcg@5 0.5577 | recall@10 0.4803 | mrr 0.7158 | 0.0048 s/query | efficiency 0.1114 | 206/209 queries judged
- Weakest categories (NDCG@5): C03 Attribute / implied meaning 0.1655, C10 Multi-constraint compositional 0.1689, C08 Dietary constraint / negation 0.2537, C18 Chicken dishes 0.2967, C02 Ingredient generalization 0.3423

### Plan (iteration 23)
- Hypothesis: Hybrid search with MiniLM-L12 and grade-boost 2.0 leads the benchmark (NDCG@5=0.8058), but the word-vector family has no recorded runs on the leaderboard, and pure neural retrievers (CrossEncoder and ColBERT) exhibit a severe blind spot on dietary queries (C08 NDCG@5 ~0.33) because their indexed item texts omit dietary metadata. First, we benchmark Phrase-Aware Soft-BM25 with ConceptNet Numberbatch to establish baseline performance for the word-vector family. Second, we update crossencoder_search.py and colbert_search.py to incorporate item['dietary'] annotations into their text representations (matching hybrid_search.py), improving retrieval accuracy across dietary constraint categories.
- Queued: run_experiment softbm25-conceptnet
- Queued: change_code Update research/search/crossencoder_search.py and research/search/colbert_search.py to include item.get('dietary') in their item text representations 

### Iteration 23: softbm25-conceptnet (SUCCESS)
- Result: `research/agent/results/softbm25-conceptnet.json` | commit `59c587a` | 23.5s
- Setup: `mkdir -p /content/scratch && [ -f /content/scratch/numberbatch-en-19.08.txt.gz ] || wget -q -O /content/scratch/numberbatch-en-19.08.txt.gz https://conceptnet.s3.amazonaws.com/downloads/2019/numberbatch/numberbatch-en-19.08.txt.gz`
- Eval args: `--engine soft_bm25 --vectors /content/scratch/numberbatch-en-19.08.txt.gz` | family `word-vector`
- ndcg@5 0.5664 | recall@10 0.5456 | mrr 0.7287 | 0.0165 s/query | efficiency 0.1129 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.1173, C08 Dietary constraint / negation 0.2396, C03 Attribute / implied meaning 0.2853, C07 Hyphenation / spacing / stop words 0.2931, C01 Cuisine type inference 0.3589

### Iteration 24: crossencoder-ms-marco-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/crossencoder-ms-marco-MiniLM-L6-v2.json` | commit `a474807` | 18.7s
- Eval args: `--engine crossencoder --model cross-encoder/ms-marco-MiniLM-L6-v2` | family `cross-encoder`
- ndcg@5 0.6569 | recall@10 0.5869 | mrr 0.8042 | 0.0563 s/query | efficiency 0.1299 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2024, C25 Occasion / meal-time 0.2648, C03 Attribute / implied meaning 0.2743, C08 Dietary constraint / negation 0.4099, C02 Ingredient generalization 0.4267

### Iteration 24: code change
**Goal**: Update research/search/crossencoder_search.py and research/search/colbert_search.py to include item.get('dietary') in their item text representations (matching hybrid_search.py), and add the ConceptNet download line to research/agent/setup_machine.sh. Verify by running evaluate.py --engine crossencoder --model cross-encoder/ms-marco-MiniLM-L6-v2.

**Summary**: Updated research/search/crossencoder_search.py and research/search/colbert_search.py to include item.get('dietary') in their item text representation matching hybrid_search.py. Added ConceptNet Numberbatch 19.08 download to research/agent/setup_machine.sh and documented it in research/agent/README.md. Verification benchmark with crossencoder ms-marco-MiniLM-L6-v2 showed NDCG@5 increased from 0.6510 to 0.6569, with dietary constraint category C08 improving significantly from 0.3316 to 0.4101.

**Files changed**:
```
 M research/agent/LEADERBOARD.md
 M research/agent/README.md
 M research/agent/setup_machine.sh
 M research/search/colbert_search.py
 M research/search/crossencoder_search.py
```

### Iteration 25: crossencoder-ms-marco-MiniLM-L6-v2 (SUCCESS)
- Result: `research/agent/results/crossencoder-ms-marco-MiniLM-L6-v2.json` | commit `2f65e1f` | 18.7s
- Eval args: `--engine crossencoder --model cross-encoder/ms-marco-MiniLM-L6-v2` | family `cross-encoder`
- ndcg@5 0.6569 | recall@10 0.5869 | mrr 0.8042 | 0.0562 s/query | efficiency 0.1299 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.2024, C25 Occasion / meal-time 0.2648, C03 Attribute / implied meaning 0.2743, C08 Dietary constraint / negation 0.4099, C02 Ingredient generalization 0.4267

### Iteration 26: crossencoder-ms-marco-MiniLM-L12-v2 (SUCCESS)
- Result: `research/agent/results/crossencoder-ms-marco-MiniLM-L12-v2.json` | commit `c84d3c8` | 25.6s
- Eval args: `--engine crossencoder --model cross-encoder/ms-marco-MiniLM-L12-v2` | family `cross-encoder`
- ndcg@5 0.6562 | recall@10 0.5834 | mrr 0.7985 | 0.089 s/query | efficiency 0.1289 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.1494, C25 Occasion / meal-time 0.2574, C03 Attribute / implied meaning 0.2657, C08 Dietary constraint / negation 0.3753, C02 Ingredient generalization 0.3814

### Plan (iteration 27)
- Hypothesis: In iteration 24, dietary metadata was added to colbert_search.py and crossencoder_search.py, yielding a significant boost on dietary constraints (C08 NDCG@5 increased from 0.3316 to 0.4099 on CrossEncoder), but ColBERT has not yet been re-evaluated with this update. Meanwhile, sbert_search.py still uses lib.data.item_text which omits dietary metadata, leaving the bi-encoder family with low scores on C08 (0.3637). We first re-run ColBERT to measure the effect of dietary metadata on late-interaction retrieval, and then update sbert_search.py to include dietary annotations in its text representation.
- Queued: run_experiment colbert-colbertv2.0
- Queued: change_code Update research/search/sbert_search.py to include item.get('dietary') in its item text representation using a local _item_text helper (matching colber

### Iteration 27: colbert-colbertv2.0 (SUCCESS)
- Result: `research/agent/results/colbert-colbertv2.0.json` | commit `b378a32` | 9.4s
- Eval args: `--engine colbert` | family `late-interaction`
- ndcg@5 0.6542 | recall@10 0.5654 | mrr 0.7981 | 0.0091 s/query | efficiency 0.1306 | 206/209 queries judged
- Weakest categories (NDCG@5): C10 Multi-constraint compositional 0.0, C03 Attribute / implied meaning 0.2252, C25 Occasion / meal-time 0.3187, C02 Ingredient generalization 0.386, C08 Dietary constraint / negation 0.3945
