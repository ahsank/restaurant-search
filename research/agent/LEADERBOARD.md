# Leaderboard

Rebuilt by `run_experiment.py` from `results/`. Seconds per query include LLM generation for
engines that replay `--rankings`, and depend on the GPU (column GPU): compare them only between
runs on the same GPU. `–` = not recorded (re-run it).

## Best per method family (by NDCG@5)

| Family | Best experiment | NDCG@5 | Recall@10 | MRR | s/query | GPU | Efficiency | Experiments |
|---|---|---|---|---|---|---|---|---|
| lexical | baseline-enhanced | 0.5566 | 0.5589 | 0.6050 | 0.0140 | – | 0.1110 | 2 |
| word-vector | softbm25-conceptnet | 0.5702 | 0.5443 | 0.7326 | 0.0166 | – | 0.1137 | 1 |
| bi-encoder | sbert-bge-base-en-v1.5 | 0.6359 | 0.5600 | 0.7974 | 0.0044 | – | 0.1271 | 3 |
| late-interaction | colbert-colbertv2.0 | 0.6713 | 0.5840 | 0.8134 | 0.0097 | – | 0.1340 | 1 |
| cross-encoder | crossencoder-bge-reranker-large | 0.7091 | 0.6102 | 0.8487 | 0.6188 | NVIDIA RTX PRO 6000 Blackwell Server Edition | 0.1262 | 4 |
| llm | hybrid-qwen2.5-7b-minilm-l12-boost2 | 0.8195 | 0.8427 | 0.8712 | 0.2033 | – | 0.1575 | 7 |
| other | (none yet) | | | | | | | 0 |

## Efficiency = NDCG@5 / (seconds per query + 5)

| # | Experiment | Family | Efficiency | NDCG@5 | s/query | GPU |
|---|---|---|---|---|---|---|
| 1 | hybrid-qwen2.5-7b-minilm-l12-boost2 | llm | 0.1575 | 0.8195 | 0.2033 | – |
| 2 | hybrid-qwen2.5-7b-minilm-l12-boost3 | llm | 0.1549 | 0.8057 | 0.2025 | – |
| 3 | hybrid-qwen2.5-7b-minilm-l6-boost2 | llm | 0.1541 | 0.8013 | 0.1987 | – |
| 4 | hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 | llm | 0.1521 | 0.7909 | 0.1987 | – |
| 5 | hybrid-qwen2.5-7b-electra-boost2 | llm | 0.1512 | 0.7888 | 0.2172 | – |
| 6 | hybrid-qwen2.5-7b-minilm-l6-strict-grade | llm | 0.1512 | 0.7858 | 0.1987 | – |
| 7 | llm-qwen2.5-7b-instruct | llm | 0.1347 | 0.6993 | 0.1914 | – |
| 8 | colbert-colbertv2.0 | late-interaction | 0.1340 | 0.6713 | 0.0097 | – |
| 9 | crossencoder-ms-marco-MiniLM-L6-v2 | cross-encoder | 0.1338 | 0.6770 | 0.0607 | – |
| 10 | crossencoder-ms-marco-MiniLM-L12-v2 | cross-encoder | 0.1323 | 0.6747 | 0.0985 | – |
| 11 | crossencoder-ms-marco-electra-base | cross-encoder | 0.1287 | 0.6806 | 0.2876 | – |
| 12 | sbert-bge-base-en-v1.5 | bi-encoder | 0.1271 | 0.6359 | 0.0044 | – |
| 13 | crossencoder-bge-reranker-large | cross-encoder | 0.1262 | 0.7091 | 0.6188 | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| 14 | softbm25-conceptnet | word-vector | 0.1137 | 0.5702 | 0.0166 | – |
| 15 | baseline-enhanced | lexical | 0.1110 | 0.5566 | 0.0140 | – |
| 16 | sbert-all-mpnet-base-v2 | bi-encoder | 0.1096 | 0.5484 | 0.0048 | – |
| 17 | sbert-all-MiniLM-L6-v2 | bi-encoder | 0.1048 | 0.5244 | 0.0032 | – |
| 18 | baseline-text | lexical | 0.0891 | 0.4456 | 0.0003 | – |
