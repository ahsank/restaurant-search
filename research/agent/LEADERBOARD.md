# Leaderboard

Rebuilt by `run_experiment.py` from `results/`. Seconds per query are measured on the Colab GPU
and include LLM generation for engines that replay `--rankings`; `–` = run before timing was
recorded (re-run it).

## Best per method family (by NDCG@5)

| Family | Best experiment | NDCG@5 | Recall@10 | MRR | s/query | Efficiency | Experiments |
|---|---|---|---|---|---|---|---|
| lexical | baseline-enhanced | 0.5484 | 0.5498 | 0.5925 | 0.0103 | 0.1095 | 2 |
| word-vector | softbm25-conceptnet | 0.5664 | 0.5456 | 0.7287 | 0.0165 | 0.1129 | 1 |
| bi-encoder | sbert-all-mpnet-base-v2 | 0.5577 | 0.4803 | 0.7158 | 0.0048 | 0.1114 | 2 |
| late-interaction | colbert-colbertv2.0 | 0.6542 | 0.5654 | 0.7981 | 0.0091 | 0.1306 | 1 |
| cross-encoder | crossencoder-ms-marco-MiniLM-L6-v2 | 0.6569 | 0.5869 | 0.8042 | 0.0562 | 0.1299 | 2 |
| llm | hybrid-qwen2.5-7b-minilm-l12-boost2 | 0.8058 | 0.8273 | 0.8637 | 0.2022 | 0.1549 | 5 |
| other | (none yet) | | | | | | 0 |

## Efficiency = NDCG@5 / (seconds per query + 5)

| # | Experiment | Family | Efficiency | NDCG@5 | s/query |
|---|---|---|---|---|---|
| 1 | hybrid-qwen2.5-7b-minilm-l12-boost2 | llm | 0.1549 | 0.8058 | 0.2022 |
| 2 | hybrid-qwen2.5-7b-minilm-l6-boost2 | llm | 0.1541 | 0.8013 | 0.1987 |
| 3 | hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 | llm | 0.1521 | 0.7909 | 0.1987 |
| 4 | hybrid-qwen2.5-7b-minilm-l6-strict-grade | llm | 0.1512 | 0.7858 | 0.1987 |
| 5 | llm-qwen2.5-7b-instruct | llm | 0.1347 | 0.6993 | 0.1914 |
| 6 | colbert-colbertv2.0 | late-interaction | 0.1306 | 0.6542 | 0.0091 |
| 7 | crossencoder-ms-marco-MiniLM-L6-v2 | cross-encoder | 0.1299 | 0.6569 | 0.0562 |
| 8 | crossencoder-ms-marco-MiniLM-L12-v2 | cross-encoder | 0.1289 | 0.6562 | 0.0890 |
| 9 | softbm25-conceptnet | word-vector | 0.1129 | 0.5664 | 0.0165 |
| 10 | sbert-all-mpnet-base-v2 | bi-encoder | 0.1114 | 0.5577 | 0.0048 |
| 11 | baseline-enhanced | lexical | 0.1095 | 0.5484 | 0.0103 |
| 12 | sbert-all-MiniLM-L6-v2 | bi-encoder | 0.1090 | 0.5452 | 0.0032 |
| 13 | baseline-text | lexical | 0.0891 | 0.4456 | 0.0003 |
