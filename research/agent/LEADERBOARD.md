# Leaderboard

Rebuilt by `run_experiment.py` from `results/`. Seconds per query are measured on the Colab GPU
and include LLM generation for engines that replay `--rankings`; `–` = run before timing was
recorded (re-run it).

## Best per method family (by NDCG@5)

| Family | Best experiment | NDCG@5 | Recall@10 | MRR | s/query | Efficiency | Experiments |
|---|---|---|---|---|---|---|---|
| lexical | baseline-enhanced | 0.5578 | 0.5564 | 0.6022 | 0.0106 | 0.1113 | 2 |
| word-vector | softbm25-conceptnet | 0.5644 | 0.5508 | 0.7250 | 0.0165 | 0.1125 | 1 |
| bi-encoder | sbert-all-MiniLM-L6-v2 | 0.5452 | 0.4786 | 0.6994 | 0.0032 | 0.1090 | 2 |
| late-interaction | colbert-colbertv2.0 | 0.6542 | 0.5654 | 0.7981 | 0.0091 | 0.1306 | 1 |
| cross-encoder | crossencoder-ms-marco-MiniLM-L6-v2 | 0.6639 | 0.5845 | 0.8122 | 0.0576 | 0.1313 | 3 |
| llm | hybrid-qwen2.5-7b-minilm-l12-boost2 | 0.8058 | 0.8273 | 0.8637 | 0.2022 | 0.1549 | 6 |
| other | (none yet) | | | | | | 0 |

## Efficiency = NDCG@5 / (seconds per query + 5)

| # | Experiment | Family | Efficiency | NDCG@5 | s/query |
|---|---|---|---|---|---|
| 1 | hybrid-qwen2.5-7b-minilm-l12-boost2 | llm | 0.1549 | 0.8058 | 0.2022 |
| 2 | hybrid-qwen2.5-7b-minilm-l12-boost3 | llm | 0.1549 | 0.8057 | 0.2025 |
| 3 | hybrid-qwen2.5-7b-minilm-l6-boost2 | llm | 0.1541 | 0.8013 | 0.1987 |
| 4 | hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 | llm | 0.1521 | 0.7909 | 0.1987 |
| 5 | hybrid-qwen2.5-7b-minilm-l6-strict-grade | llm | 0.1512 | 0.7858 | 0.1987 |
| 6 | llm-qwen2.5-7b-instruct | llm | 0.1347 | 0.6993 | 0.1914 |
| 7 | crossencoder-ms-marco-MiniLM-L6-v2 | cross-encoder | 0.1313 | 0.6639 | 0.0576 |
| 8 | colbert-colbertv2.0 | late-interaction | 0.1306 | 0.6542 | 0.0091 |
| 9 | crossencoder-ms-marco-MiniLM-L12-v2 | cross-encoder | 0.1289 | 0.6562 | 0.0890 |
| 10 | crossencoder-ms-marco-electra-base | cross-encoder | 0.1259 | 0.6625 | 0.2603 |
| 11 | softbm25-conceptnet | word-vector | 0.1125 | 0.5644 | 0.0165 |
| 12 | baseline-enhanced | lexical | 0.1113 | 0.5578 | 0.0106 |
| 13 | sbert-all-MiniLM-L6-v2 | bi-encoder | 0.1090 | 0.5452 | 0.0032 |
| 14 | sbert-all-mpnet-base-v2 | bi-encoder | 0.1088 | 0.5447 | 0.0048 |
| 15 | baseline-text | lexical | 0.0891 | 0.4456 | 0.0003 |
