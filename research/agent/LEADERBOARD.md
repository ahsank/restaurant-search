# Leaderboard

Rebuilt by `run_experiment.py` from `results/`. Seconds per query include LLM generation for
engines that replay `--rankings`, and depend on the GPU (column GPU): compare them only between
runs on the same GPU. `–` = not recorded (re-run it).

## Best per method family (by NDCG@5)

| Family | Best experiment | NDCG@5 | Recall@10 | MRR | s/query | GPU | Efficiency | Experiments |
|---|---|---|---|---|---|---|---|---|
| lexical | baseline-enhanced | 0.6397 | 0.5936 | 0.7656 | 0.0640 | NVIDIA L4 | 0.1263 | 2 |
| word-vector | softbm25-conceptnet | 0.5704 | 0.5279 | 0.7318 | 0.0370 | NVIDIA L4 | 0.1133 | 1 |
| bi-encoder | sbert-bge-base-en-v1.5 | 0.6359 | 0.5600 | 0.7974 | 0.0044 | – | 0.1271 | 5 |
| late-interaction | colbert-colbertv2.0 | 0.6583 | 0.5733 | 0.8036 | 0.0310 | Tesla T4 | 0.1309 | 1 |
| cross-encoder | crossencoder-bge-reranker-v2-m3 | 0.7242 | 0.6165 | 0.8745 | 0.6148 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1290 | 5 |
| llm | hybrid-qwen2.5-32b-bge-reranker-v2-m3 | 0.8369 | 0.7972 | 0.9089 | 0.4143 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1546 | 11 |
| other | (none yet) | | | | | | | 0 |

## Efficiency = NDCG@5 / (seconds per query + 5)

| # | Experiment | Family | Efficiency | NDCG@5 | s/query | GPU |
|---|---|---|---|---|---|---|
| 1 | hybrid-qwen2.5-14b-minilm-l12-boost2 | llm | 0.1581 | 0.8203 | 0.1894 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 2 | hybrid-qwen2.5-7b-minilm-l12-boost2 | llm | 0.1575 | 0.8195 | 0.2033 | – |
| 3 | hybrid-qwen2.5-7b-minilm-l12-boost3 | llm | 0.1549 | 0.8057 | 0.2025 | – |
| 4 | hybrid-qwen2.5-32b-bge-reranker-v2-m3 | llm | 0.1546 | 0.8369 | 0.4143 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 5 | hybrid-qwen2.5-7b-minilm-l6-boost2 | llm | 0.1541 | 0.8013 | 0.1987 | – |
| 6 | hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 | llm | 0.1521 | 0.7909 | 0.1987 | – |
| 7 | hybrid-qwen2.5-7b-bge-reranker-large | llm | 0.1519 | 0.7978 | 0.2511 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 8 | hybrid-qwen2.5-32b-minilm-l12-boost2 | llm | 0.1518 | 0.8168 | 0.3803 | NVIDIA L4 |
| 9 | hybrid-qwen2.5-7b-electra-boost2 | llm | 0.1512 | 0.7888 | 0.2172 | – |
| 10 | hybrid-qwen2.5-7b-minilm-l6-strict-grade | llm | 0.1512 | 0.7858 | 0.1987 | – |
| 11 | hybrid-qwen2.5-7b-bge-reranker-v2-m3 | llm | 0.1444 | 0.7976 | 0.5243 | NVIDIA L4 |
| 12 | crossencoder-ms-marco-MiniLM-L6-v2 | cross-encoder | 0.1338 | 0.6770 | 0.0607 | – |
| 13 | crossencoder-ms-marco-MiniLM-L12-v2 | cross-encoder | 0.1323 | 0.6747 | 0.0985 | – |
| 14 | colbert-colbertv2.0 | late-interaction | 0.1309 | 0.6583 | 0.0310 | Tesla T4 |
| 15 | crossencoder-bge-reranker-v2-m3 | cross-encoder | 0.1290 | 0.7242 | 0.6148 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 16 | crossencoder-ms-marco-electra-base | cross-encoder | 0.1287 | 0.6806 | 0.2876 | – |
| 17 | sbert-bge-base-en-v1.5 | bi-encoder | 0.1271 | 0.6359 | 0.0044 | – |
| 18 | baseline-enhanced | lexical | 0.1263 | 0.6397 | 0.0640 | NVIDIA L4 |
| 19 | crossencoder-bge-reranker-large | cross-encoder | 0.1262 | 0.7091 | 0.6188 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 20 | sbert-mxbai-embed-large | bi-encoder | 0.1249 | 0.6278 | 0.0271 | NVIDIA L4 |
| 21 | sbert-bge-large-en-v1.5 | bi-encoder | 0.1237 | 0.6191 | 0.0072 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 22 | softbm25-conceptnet | word-vector | 0.1133 | 0.5704 | 0.0370 | NVIDIA L4 |
| 23 | sbert-all-mpnet-base-v2 | bi-encoder | 0.1096 | 0.5484 | 0.0048 | – |
| 24 | sbert-all-MiniLM-L6-v2 | bi-encoder | 0.1048 | 0.5244 | 0.0032 | – |
| 25 | baseline-text | lexical | 0.0891 | 0.4456 | 0.0003 | – |
