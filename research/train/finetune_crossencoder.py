"""
Approach 6 training: finetune a pretrained cross-encoder reranker on the same
leak-free triples used by Approach 5 variants 2 and 3 —
research/data_gen/synthetic_triples.jsonl (structural mining over every
restaurant in data/menus/, never touches data/queries/) plus
research/data_gen/gap_fill_triples.jsonl (30 reworded patches for the worst
benchmark queries).

The triples are turned into labeled (query, item) pairs in memory at startup —
nothing is written to the repo unless --dump-pairs is given:

  (anchor, positive)          -> 1.0
  (anchor, hard negative)     -> 0.0
  (anchor, random item) x N   -> 0.0   (--random-negatives, default 3)

Why random negatives on top of the explicit hard ones: the synthetic set has
only ~205 distinct positive items and its hard negatives are all near-misses
of the same dish type. A cross-encoder trained on those alone never sees an
"obviously wrong" pair and can lose the coarse calibration it got from
MS MARCO. Random items are drawn from every restaurant in data/menus/,
excluding any item text used as a positive for that anchor. They may
occasionally be a true match — accepted label noise, same as in-batch
negatives in Approach 5.

Pairs are deduplicated per (anchor, item): the synthetic set reuses the same
positive/negative across several paraphrase anchors, but the same anchor+item
never needs to appear twice. If one pair is labeled both ways (the same text
is a positive in one triple and a hard negative in another), the positive
label wins.

Loss is BinaryCrossEntropyLoss — pointwise relevance on a single logit, the
standard sentence-transformers recipe for finetuning a reranker on hard
negatives. Unlike the bi-encoder's InfoNCE, a cross-encoder scores each pair
independently, so there are no in-batch negatives to exploit; the random
negatives above play that role.

Usage:
    python research/train/finetune_crossencoder.py
    python research/train/finetune_crossencoder.py --epochs 2 --random-negatives 5
    python research/train/finetune_crossencoder.py --dump-pairs /tmp/ce_pairs.jsonl

Evaluate afterwards on the full benchmark (no held-out split needed — see
"Leakage" under Approach 6 in research/APPROACHES.md):
    python research/search/evaluate.py --engine crossencoder --model models/crossencoder-synthetic-plus-gapfill
"""

import argparse
import json
import random
import sys
from pathlib import Path

import torch
from datasets import Dataset
from sentence_transformers.cross_encoder import (
    CrossEncoder,
    CrossEncoderTrainer,
    CrossEncoderTrainingArguments,
)
from sentence_transformers.cross_encoder.losses import BinaryCrossEntropyLoss

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "research"))
from lib.data import item_text, load_data

_DATA_GEN = _ROOT / "research" / "data_gen"
_DEFAULT_TRIPLES = [_DATA_GEN / "synthetic_triples.jsonl", _DATA_GEN / "gap_fill_triples.jsonl"]
_DEFAULT_BASE_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
_DEFAULT_OUTPUT = _ROOT / "models" / "crossencoder-synthetic-plus-gapfill"


def load_triples(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        rows.extend(json.loads(line) for line in open(path, encoding="utf-8"))
    return rows


def build_pairs(triples: list[dict], corpus: list[str], random_negatives: int, seed: int) -> list[dict]:
    """Expand triples into deduplicated (query, passage, label) rows."""
    rng = random.Random(seed)
    labels: dict[tuple[str, str], float] = {}
    positives_by_anchor: dict[str, set[str]] = {}

    for t in triples:
        positives_by_anchor.setdefault(t["anchor"], set()).add(t["positive"])

    for t in triples:
        a = t["anchor"]
        labels[(a, t["positive"])] = 1.0
        labels.setdefault((a, t["negative"]), 0.0)

    for a, positives in positives_by_anchor.items():
        drawn = 0
        while drawn < random_negatives:
            text = rng.choice(corpus)
            if text in positives or (a, text) in labels:
                continue
            labels[(a, text)] = 0.0
            drawn += 1

    pairs = [{"query": a, "passage": p, "label": y} for (a, p), y in labels.items()]
    rng.shuffle(pairs)
    return pairs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--triples", type=Path, nargs="+", default=_DEFAULT_TRIPLES,
                        help="One or more triples JSONL files, concatenated "
                             "(default: synthetic_triples.jsonl + gap_fill_triples.jsonl)")
    parser.add_argument("--base-model", default=_DEFAULT_BASE_MODEL,
                        help=f"Pretrained cross-encoder to finetune (default: {_DEFAULT_BASE_MODEL})")
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT,
                        help=f"Where to save the finetuned model (default: {_DEFAULT_OUTPUT})")
    parser.add_argument("--random-negatives", type=int, default=3,
                        help="Random corpus items added as negatives per distinct anchor (default: 3)")
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--eval-fraction", type=float, default=0.1,
                        help="Held-out fraction of pairs for eval loss during training (default: 0.1)")
    parser.add_argument("--dump-pairs", type=Path, default=None,
                        help="Optionally write the generated pairs to this JSONL path for inspection")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"Loading triples from {', '.join(str(p) for p in args.triples)}...", end=" ", flush=True)
    triples = load_triples(args.triples)
    print(f"{len(triples)} triples")

    _, menus = load_data()  # every restaurant — the random-negative pool, not the eval scope
    corpus = sorted({item_text(item) for items in menus.values() for item in items})

    pairs = build_pairs(triples, corpus, args.random_negatives, args.seed)
    n_pos = sum(1 for p in pairs if p["label"] == 1.0)
    print(f"  {len(pairs)} pairs ({n_pos} positive, {len(pairs) - n_pos} negative) "
          f"from a {len(corpus)}-item negative pool")

    if args.dump_pairs:
        with open(args.dump_pairs, "w", encoding="utf-8") as f:
            for p in pairs:
                f.write(json.dumps(p) + "\n")
        print(f"  wrote pairs to {args.dump_pairs}")

    dataset = Dataset.from_list(pairs)
    split = dataset.train_test_split(test_size=args.eval_fraction, seed=args.seed)
    train_dataset, eval_dataset = split["train"], split["test"]
    print(f"  train={len(train_dataset)}  eval={len(eval_dataset)}")

    print(f"Loading base model '{args.base_model}'...", end=" ", flush=True)
    model = CrossEncoder(args.base_model, num_labels=1)
    print("done")

    # pos_weight balances the ~1:4 positive:negative ratio so the loss isn't
    # dominated by easy random negatives.
    loss = BinaryCrossEntropyLoss(model, pos_weight=torch.tensor((len(pairs) - n_pos) / max(n_pos, 1)))

    training_args = CrossEncoderTrainingArguments(
        output_dir=str(args.output_dir / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_steps=0.1,  # transformers v5+: fractional warmup_steps replaces the deprecated warmup_ratio
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        logging_steps=20,
        seed=args.seed,
    )

    trainer = CrossEncoderTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        loss=loss,
    )
    trainer.train()

    model.save_pretrained(str(args.output_dir))
    print(f"\nSaved finetuned cross-encoder to {args.output_dir}")
    print(f"Evaluate with:\n  python research/search/evaluate.py --engine crossencoder --model {args.output_dir}")
