# Leaderboard

Rebuilt by `run_experiment.py` from `results/`. Seconds per query include LLM generation for
engines that replay `--rankings`, and depend on the GPU (column GPU): compare them only between
runs on the same GPU. `–` = not recorded (re-run it).

## Best per method family (by NDCG@5)

| Family | Best experiment | NDCG@5 | Recall@10 | MRR | s/query | GPU | Efficiency | Experiments |
|---|---|---|---|---|---|---|---|---|
| lexical | baseline-enhanced | 0.6514 | 0.5980 | 0.7740 | 0.0267 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1296 | 2 |
| word-vector | softbm25-conceptnet | 0.5741 | 0.5231 | 0.7340 | 0.0125 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1145 | 1 |
| bi-encoder | sbert-gte-large | 0.6621 | 0.5570 | 0.8117 | 0.0097 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1322 | 6 |
| late-interaction | colbert-colbertv2.0 | 0.6583 | 0.5733 | 0.8036 | 0.0310 | Tesla T4 | 0.1309 | 1 |
| cross-encoder | crossencoder-bge-reranker-v2-m3 | 0.7406 | 0.6120 | 0.8906 | 0.6159 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1319 | 5 |
| llm | hybrid-qwen2.5-32b-bge-reranker-v2-m3 | 0.8428 | 0.8126 | 0.9133 | 0.3964 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1562 | 14 |
| other | (none yet) | | | | | | | 0 |

## Efficiency = NDCG@5 / (seconds per query + 5)

| # | Experiment | Family | Efficiency | NDCG@5 | s/query | GPU |
|---|---|---|---|---|---|---|
| 1 | hybrid-qwen2.5-7b-minilm-l6-boost2 | llm | 0.1633 | 0.8323 | 0.0977 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 2 | hybrid-qwen2.5-7b-minilm-l12-boost3 | llm | 0.1624 | 0.8286 | 0.1012 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 3 | hybrid-qwen2.5-7b-minilm-l12-boost2 | llm | 0.1622 | 0.8277 | 0.1012 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 4 | hybrid-qwen2.5-14b-minilm-l12-boost2 | llm | 0.1613 | 0.8361 | 0.1841 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 5 | hybrid-qwen2.5-32b-minilm-l12-boost2 | llm | 0.1572 | 0.8402 | 0.3436 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 6 | hybrid-qwen2.5-32b-bge-reranker-v2-m3 | llm | 0.1562 | 0.8428 | 0.3964 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 7 | hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 | llm | 0.1551 | 0.8067 | 0.2008 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 8 | hybrid-qwen2.5-7b-minilm-l6-strict-grade | llm | 0.1526 | 0.7936 | 0.2007 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 9 | hybrid-qwen2.5-7b-bge-reranker-v2-m3 | llm | 0.1513 | 0.7969 | 0.2674 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 10 | hybrid-qwen2.5-7b-electra-boost2 | llm | 0.1500 | 0.7827 | 0.2189 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 11 | hybrid-qwen2.5-7b-bge-reranker-large | llm | 0.1495 | 0.7877 | 0.2676 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 12 | llm-qwen2.5-32b-instruct | llm | 0.1459 | 0.7780 | 0.3316 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 13 | llm-qwen2.5-14b-instruct | llm | 0.1416 | 0.7326 | 0.1746 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 14 | llm-qwen2.5-7b-instruct | llm | 0.1391 | 0.7080 | 0.0900 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 15 | crossencoder-ms-marco-MiniLM-L6-v2 | cross-encoder | 0.1365 | 0.6904 | 0.0563 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 16 | crossencoder-ms-marco-MiniLM-L12-v2 | cross-encoder | 0.1354 | 0.6883 | 0.0823 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 17 | crossencoder-ms-marco-electra-base | cross-encoder | 0.1327 | 0.6905 | 0.2052 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 18 | sbert-gte-large | bi-encoder | 0.1322 | 0.6621 | 0.0097 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 19 | crossencoder-bge-reranker-v2-m3 | cross-encoder | 0.1319 | 0.7406 | 0.6159 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 20 | colbert-colbertv2.0 | late-interaction | 0.1309 | 0.6583 | 0.0310 | Tesla T4 |
| 21 | baseline-enhanced | lexical | 0.1296 | 0.6514 | 0.0267 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 22 | sbert-bge-base-en-v1.5 | bi-encoder | 0.1294 | 0.6477 | 0.0048 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 23 | sbert-mxbai-embed-large | bi-encoder | 0.1287 | 0.6446 | 0.0097 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 24 | crossencoder-bge-reranker-large | cross-encoder | 0.1278 | 0.7181 | 0.6175 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 25 | sbert-bge-large-en-v1.5 | bi-encoder | 0.1263 | 0.6325 | 0.0073 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 26 | softbm25-conceptnet | word-vector | 0.1145 | 0.5741 | 0.0125 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 27 | sbert-all-mpnet-base-v2 | bi-encoder | 0.1120 | 0.5608 | 0.0050 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 28 | sbert-all-MiniLM-L6-v2 | bi-encoder | 0.1079 | 0.5398 | 0.0035 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 29 | baseline-text | lexical | 0.0912 | 0.4562 | 0.0003 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
