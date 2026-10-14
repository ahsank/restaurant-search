# Leaderboard

Rebuilt by `run_experiment.py` from `results/`. Seconds per query are measured on the Colab GPU
and include LLM generation for engines that replay `--rankings`; `–` = run before timing was
recorded (re-run it).

## Best per method family (by NDCG@5)

| Family | Best experiment | NDCG@5 | Recall@10 | MRR | s/query | Efficiency | Experiments |
|---|---|---|---|---|---|---|---|
| lexical | baseline-enhanced | 0.5484 | 0.5498 | 0.5925 | 0.0103 | 0.1095 | 2 |
| word-vector | (none yet) | | | | | | 0 |
| bi-encoder | sbert-all-MiniLM-L6-v2 | 0.5592 | 0.4883 | 0.7093 | – | – | 2 |
| late-interaction | colbert-colbertv2.0 | 0.6422 | 0.5616 | 0.7851 | 0.0095 | 0.1282 | 1 |
| cross-encoder | crossencoder-ms-marco-MiniLM-L6-v2 | 0.6510 | 0.5874 | 0.7989 | 0.0549 | 0.1288 | 2 |
| llm | hybrid-qwen2.5-7b-minilm-l12-boost2 | 0.8058 | 0.8273 | 0.8637 | 0.2022 | 0.1549 | 5 |
| other | (none yet) | | | | | | 0 |

## Efficiency = NDCG@5 / (seconds per query + 5)

| # | Experiment | Family | Efficiency | NDCG@5 | s/query |
|---|---|---|---|---|---|
| 1 | hybrid-qwen2.5-7b-minilm-l12-boost2 | llm | 0.1549 | 0.8058 | 0.2022 |
| 2 | hybrid-qwen2.5-7b-minilm-l6-boost2 | llm | 0.1541 | 0.8013 | 0.1987 |
| 3 | crossencoder-ms-marco-MiniLM-L6-v2 | cross-encoder | 0.1288 | 0.6510 | 0.0549 |
| 4 | colbert-colbertv2.0 | late-interaction | 0.1282 | 0.6422 | 0.0095 |
| 5 | crossencoder-ms-marco-MiniLM-L12-v2 | cross-encoder | 0.1270 | 0.6462 | 0.0872 |
| 6 | baseline-enhanced | lexical | 0.1095 | 0.5484 | 0.0103 |
| 7 | baseline-text | lexical | 0.0891 | 0.4456 | 0.0003 |
| 8 | hybrid-qwen2.5-7b-minilm-l6-strict-grade | llm | – | 0.7858 | – |
| 9 | hybrid-qwen2.5-7b-ms-marco-MiniLM-L6-v2 | llm | – | 0.7840 | – |
| 10 | llm-qwen2.5-7b-instruct | llm | – | 0.6993 | – |
| 11 | sbert-all-MiniLM-L6-v2 | bi-encoder | – | 0.5592 | – |
| 12 | sbert-all-mpnet-base-v2 | bi-encoder | – | 0.5577 | – |
