"""
Why does BERT rank "Juice" above "Shrimp & Clam Pasta" for "shellfish pasta"?

This script uses the same BertSubwordEncoder logic as soft_bm25_search.py:
  - tokenise each text with BERT WordPiece
  - average subword hidden states into per-word vectors (BERT last hidden state)
  - score = MaxSim: for each query word, take the max cosine over all item words

Run:
    conda run -n search python research/experiment/bert_maxsim.py
"""

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

# ── texts under investigation ─────────────────────────────────────────────────
QUERY = "shellfish pasta"

ITEMS = [
    "Juice",                                # Great China Restaurant — irrelevant
    "Shrimp and clam pasta",               # expected match
    "Shrimp Pasta with Cajun cream sauce", # another expected match
]

# ── load BERT ─────────────────────────────────────────────────────────────────
MODEL_NAME = "bert-base-uncased"
print(f"Loading {MODEL_NAME}…", flush=True)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()


# ── encode: WordPiece → per-word unit vectors ─────────────────────────────────
def encode(text: str) -> tuple[list[str], np.ndarray]:
    """
    Returns (words, unit-normalised matrix of shape (n_words, 768)).
    Matches BertSubwordEncoder in soft_bm25_search.py exactly.
    """
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        hidden = model(**inputs).last_hidden_state[0]   # (seq_len, 768)

    toks = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

    words, vecs = [], []
    cur_word, cur_vecs = "", []

    for tok, vec in zip(toks[1:-1], hidden[1:-1]):     # skip [CLS] and [SEP]
        if tok.startswith("##"):
            cur_word += tok[2:]
            cur_vecs.append(vec)
        else:
            if cur_word:
                avg = torch.stack(cur_vecs).mean(0).numpy()
                norm = float(np.linalg.norm(avg))
                if norm > 1e-9:
                    words.append(cur_word)
                    vecs.append(avg / norm)
            cur_word, cur_vecs = tok, [vec]

    if cur_word:
        avg = torch.stack(cur_vecs).mean(0).numpy()
        norm = float(np.linalg.norm(avg))
        if norm > 1e-9:
            words.append(cur_word)
            vecs.append(avg / norm)

    return words, np.stack(vecs).astype(np.float32) if vecs else np.zeros((0, 768))


# ── MaxSim scorer ─────────────────────────────────────────────────────────────
def maxsim_score(
    query_words: list[str],
    query_vecs: np.ndarray,
    item_words: list[str],
    item_vecs: np.ndarray,
    threshold: float = 0.5,
) -> float:
    """
    Sum of per-query-word max-cosine over item words (soft-BM25 'plus' combiner).
    Returns total score and prints per-word breakdown.
    """
    total = 0.0
    for qw, qv in zip(query_words, query_vecs):
        sims = item_vecs @ qv          # (n_item_words,)
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        best_word = item_words[best_idx]
        soft_tf = best_sim if best_sim >= threshold else 0.0
        flag = "✓" if soft_tf > 0 else "✗"
        print(f"    q:'{qw}' → best match '{best_word}' cos={best_sim:+.4f} "
              f"soft_tf={soft_tf:.4f} {flag}")
        total += soft_tf
    return total


# ── run ───────────────────────────────────────────────────────────────────────
print(f"\nQuery: '{QUERY}'")
q_words, q_vecs = encode(QUERY)
print(f"Query words: {q_words}")

for item_text in ITEMS:
    i_words, i_vecs = encode(item_text)
    print(f"\n{'─'*60}")
    print(f"Item: '{item_text}'")
    print(f"Item words: {i_words}")
    score = maxsim_score(q_words, q_vecs, i_words, i_vecs)
    print(f"  → Total score: {score:.4f}")

print(f"\n{'='*60}")
print("Key observation: if Juice scores ≥ Shrimp Pasta, BERT last-hidden-state")
print("vectors are not a reliable similarity space for cross-sentence token")
print("comparison. Vectors trained on masked-LM are not calibrated for this.")
