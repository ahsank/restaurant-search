"""
Approach 5 training: finetune a bi-encoder on the (anchor, positive, negative)
triples produced by research/data_gen/mine_hard_negatives.py.

Loss is MultipleNegativesRankingLoss — this *is* InfoNCE (softmax cross-entropy
over one positive vs. every other negative in the batch, plus each row's
explicit hard-negative column) — see the "Loss" note under Approach 5 in
research/APPROACHES.md for why this is preferred over a classifier or Triplet
Loss. batch_sampler=NO_DUPLICATES avoids putting the same text on both sides
of a pair within a batch, which would otherwise create false in-batch
negatives (several triples in triples.jsonl share the same positive item
across near-duplicate queries).

Usage:
    python research/train/finetune_biencoder.py
    python research/train/finetune_biencoder.py --base-model all-MiniLM-L6-v2 --epochs 10
    python research/train/finetune_biencoder.py --triples research/data_gen/triples.jsonl \
        --output-dir models/finetuned-all-MiniLM-L6-v2

After training, evaluate with the existing benchmark harness — no separate
eval code needed here, since SentenceTransformer(path) accepts a local
directory exactly like a hub model name:
    python research/search/evaluate.py --engine sbert --model models/finetuned-all-MiniLM-L6-v2
"""

import argparse
import json
from pathlib import Path

from datasets import Dataset
from sentence_transformers import (
    SentenceTransformer,
    SentenceTransformerTrainer,
    SentenceTransformerTrainingArguments,
)
from sentence_transformers.losses import MultipleNegativesRankingLoss
from sentence_transformers.training_args import BatchSamplers

_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_TRIPLES = _ROOT / "research" / "data_gen" / "triples.jsonl"
_DEFAULT_BASE_MODEL = "all-MiniLM-L6-v2"


def load_triples(paths: list[Path]) -> Dataset:
    rows = []
    for path in paths:
        rows.extend(json.loads(line) for line in open(path, encoding="utf-8"))
    return Dataset.from_dict({
        "anchor": [r["anchor"] for r in rows],
        "positive": [r["positive"] for r in rows],
        "negative": [r["negative"] for r in rows],
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--triples", type=Path, nargs="+", default=[_DEFAULT_TRIPLES],
                        help=f"One or more triples JSONL files, concatenated (default: {_DEFAULT_TRIPLES})")
    parser.add_argument("--base-model", default=_DEFAULT_BASE_MODEL,
                        help=f"Pretrained sentence-transformers model to finetune (default: {_DEFAULT_BASE_MODEL})")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Where to save the finetuned model (default: models/finetuned-<base-model>)")
    parser.add_argument("--epochs", type=float, default=10.0)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--eval-fraction", type=float, default=0.1,
                        help="Held-out fraction for eval loss during training (default: 0.1)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_dir = args.output_dir or (_ROOT / "models" / f"finetuned-{args.base_model.split('/')[-1]}")

    print(f"Loading triples from {', '.join(str(p) for p in args.triples)}...", end=" ", flush=True)
    dataset = load_triples(args.triples)
    print(f"{len(dataset)} triples")

    split = dataset.train_test_split(test_size=args.eval_fraction, seed=args.seed)
    train_dataset, eval_dataset = split["train"], split["test"]
    print(f"  train={len(train_dataset)}  eval={len(eval_dataset)}")

    print(f"Loading base model '{args.base_model}'...", end=" ", flush=True)
    model = SentenceTransformer(args.base_model)
    print("done")

    loss = MultipleNegativesRankingLoss(model)

    training_args = SentenceTransformerTrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_steps=0.1,  # transformers v5+: fractional warmup_steps replaces the deprecated warmup_ratio
        batch_sampler=BatchSamplers.NO_DUPLICATES,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        logging_steps=20,
        seed=args.seed,
    )

    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        loss=loss,
    )
    trainer.train()

    model.save_pretrained(str(output_dir))
    print(f"\nSaved finetuned model to {output_dir}")
    print(f"Evaluate with:\n  python research/search/evaluate.py --engine sbert --model {output_dir}")
