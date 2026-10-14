"""
Approach 3.5: Phrase-Aware Soft-BM25 using word/phrase embeddings.

Key idea: replace exact term-frequency counting in BM25 with a soft maximum
cosine similarity (MaxSim), and pre-tokenise text into phrase units so that
"oyster sauce" is treated as one semantic token, distinct from "oyster" alone.

Three pluggable components — swap any independently:

  PhraseTokenizer  tokenize(text) -> list[str]
    Converts text into underscore-joined phrase tokens via Forward Maximum
    Matching. Swap phrase_vocab (a set[str] of space-separated phrases) to
    change phrase detection: use gensim Phrases, a curated food glossary,
    or set it to empty to disable phrase detection entirely.

  VectorStore      lookup(token) -> np.ndarray | None
    Maps a token (possibly underscore-joined) to a unit-normalised vector.
    Direct lookup first; falls back to composing component word vectors.
    Swap raw_vectors (a dict[str, ndarray]) to use a different model:
    GloVe, FastText, Word2Vec Google News phrases, etc.

  Score parameters  similarity_threshold, k1, b
    Control BM25 soft-TF behaviour; tune on the benchmark.

    b (document-length normalization, default 0.0): with continuous soft-tf
    in [0,1] instead of BM25's usual raw integer counts, b>0 systematically
    over-rewards short documents — a mediocre fuzzy match on a 3-token item
    (just name + category) can outscore an exact match on an 11-token item
    with a real description, purely because of the length term. Benchmark
    sweep (b=0.0 vs 0.25/0.5/0.75/1.0, combiner=bm25) found NDCG@5 dropping
    monotonically as b increases (0.507 -> 0.204), so b=0 is now the default.

    k1 (saturation steepness, default 2.0): matters much less than b — at
    b=0, NDCG@5 only moved between 0.498 and 0.508 across k1 in [0.1, 20],
    plateauing for k1 >= 3. 2.0 sits in that plateau, close to the shipped
    default of 1.5; not worth tuning further without new benchmark queries.

  Combiner and spell-correct: bm25 (with b=0, k1=2.0 above) + --spell-correct
    beats every other combiner/spell-correct combination measured, including
    the `plus` combiner that was previously recommended in this file's
    header comment — NDCG@5 0.5410 vs. 0.5281 for plus+spell-correct, on the
    209-query / 8-restaurant benchmark. Both are now on by default
    (--combiner already defaulted to bm25; --spell-correct now does too).
    Use --no-spell-correct to disable, or --combiner plus to reproduce the
    old recommendation.

Default implementation uses ConceptNet Numberbatch (English), which serves as
both the phrase vocabulary and the vector source from a single ~75 MB file.

Item text includes name, description, category, menu type, and dietary annotations
(matching the representation used in hybrid, crossencoder, colbert, and sbert search).

Download:
  https://conceptnet.s3.amazonaws.com/downloads/2019/numberbatch/numberbatch-en-19.08.txt.gz

Usage:
  python soft_bm25_search.py --vectors /path/to/numberbatch-en-19.08.txt.gz seafood italian
  python soft_bm25_search.py --vectors /path/to/numberbatch-en-19.08.txt "oyster"
  python soft_bm25_search.py --vectors /path/to/numberbatch-en-19.08.txt --threshold 0.4 spicy noodles
  python soft_bm25_search.py --vectors /path/to/numberbatch-en-19.08.txt --b 0.75 --k1 1.5 --no-spell-correct --combiner plus pizza   # reproduce old defaults
"""

import argparse
import gzip
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))
from lib.data import load_data, judged_restaurant_ids, restaurant_scope_cli_args


def cli_args() -> argparse.ArgumentParser:
    """
    Reusable CLI-flag fragment for this module's scoring/segmentation parameters.

    Any script can add these flags without redefining them by passing
    `parents=[cli_args()]` to its own ArgumentParser — engines.build_arg_parser()
    does this only when this engine is selected.
    `add_help=False` is required on parent parsers (argparse would otherwise
    register -h/--help twice and raise a conflict).
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--segmenter",
        choices=["fmm", "spacy_bert", "bert_subword"],
        default="fmm",
        help=(
            "Tokeniser/segmenter: "
            "fmm (ConceptNet FMM, default), "
            "spacy_bert (spaCy noun chunks + BERT contextual vectors), "
            "bert_subword (BERT WordPiece + BERT contextual vectors)"
        ),
    )
    parser.add_argument(
        "--vectors",
        help="Path to ConceptNet Numberbatch txt or txt.gz (required for --segmenter fmm)",
    )
    parser.add_argument(
        "--max-phrase-len", type=int, default=3,
        help="Max words to merge into a phrase token (fmm only, default 3)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5,
        help="Min cosine similarity to count as a soft match (default 0.5)",
    )
    parser.add_argument(
        "--k1", type=float, default=2.0,
        help="BM25 saturation steepness for --combiner bm25 (default 2.0; barely matters, see module docstring)",
    )
    parser.add_argument(
        "--b", type=float, default=0.0,
        help="BM25 document-length normalization for --combiner bm25 (default 0.0 — see module docstring for why)",
    )
    parser.add_argument(
        "--composition", choices=["mean", "idf_mean"], default="mean",
        help="Phrase vector composition for fmm (default mean)",
    )
    parser.add_argument(
        "--combiner", choices=["bm25", "plus", "product", "min"], default="bm25",
        help=(
            "How to combine per-term scores: "
            "bm25 (IDF-weighted sum, OR), plus (raw sum, OR), "
            "product (AND), min (AND); default: bm25"
        ),
    )
    parser.add_argument(
        "--spell-correct", action="store_true", dest="spell_correct", default=True,
        help="Spell-correct query tokens that have no embedding (uses pyspellchecker). "
             "On by default — benchmark sweep found bm25+b=0+spell-correct beats every "
             "other combiner/spell-correct combination measured. Use --no-spell-correct to disable.",
    )
    parser.add_argument(
        "--no-spell-correct", action="store_false", dest="spell_correct",
        help="Disable spell correction (see --spell-correct).",
    )
    return parser


# ── Text normalisation ─────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Lowercase and strip combining diacritics (à→a, é→e, ñ→n, …)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# ── Phrase tokeniser ───────────────────────────────────────────────────────────

class PhraseTokenizer:
    """
    Forward Maximum Matching (FMM) phrase tokeniser.

    Scans left-to-right and greedily takes the longest matching phrase
    (up to max_phrase_len words) whose normalised form appears in phrase_vocab.
    Falls back to a single word when no longer phrase matches.

    Swap points:
      phrase_vocab   — set[str] of space-separated phrases (e.g. "oyster sauce").
                       Build from ConceptNet multi-word entries, Word2Vec phrases
                       vocabulary, gensim Phraser output, or a hand-curated list.
      max_phrase_len — cap to control how many words can merge into one token.

    Returns underscore-joined tokens: "oyster sauce" → "oyster_sauce".
    """

    def __init__(self, phrase_vocab: set[str], max_phrase_len: int = 3):
        self.phrase_vocab = phrase_vocab
        self.max_phrase_len = max_phrase_len

    # Punctuation stripped from word boundaries; hyphens kept (pan-fried, gluten-free).
    _STRIP = str.maketrans("", "", ".,;:!?()[]{}\"'`—–&")

    def tokenize(self, text: str) -> list[str]:
        raw = normalize(text).split()
        words = [w.translate(self._STRIP) for w in raw]
        words = [w for w in words if w]   # drop anything that became empty
        tokens: list[str] = []
        i = 0
        while i < len(words):
            matched = False
            for length in range(min(self.max_phrase_len, len(words) - i), 1, -1):
                phrase = " ".join(words[i : i + length])
                if phrase in self.phrase_vocab:
                    tokens.append(phrase.replace(" ", "_"))
                    i += length
                    matched = True
                    break
            if not matched:
                tokens.append(words[i])
                i += 1
        return tokens


# ── Vector store ───────────────────────────────────────────────────────────────

class VectorStore:
    """
    Token → unit-normalised embedding vector.

    Lookup order:
      1. Direct key lookup (e.g. "oyster_sauce" → trained vector).
      2. Composition fallback: weighted average of component word vectors,
         used when a phrase token has no direct entry in the model.

    Swap points:
      raw_vectors  — dict[str, np.ndarray] with underscore-joined keys.
                     Replace with GloVe, FastText, Word2Vec phrases, etc.
                     Keys must be normalised (lowercase, no accents).
      composition  — how to combine component vectors for unseen phrases:
                     "mean"     : uniform average
                     "idf_mean" : downweights common words (sauce, with, …)
      token_idf    — dict[str, float] used by idf_mean; pass the corpus IDF
                     computed by build_index().
    """

    def __init__(
        self,
        raw_vectors: dict[str, np.ndarray],
        composition: str = "mean",
        token_idf: dict[str, float] | None = None,
    ):
        self._vecs = raw_vectors
        self._composition = composition
        self._token_idf = token_idf or {}
        self._cache: dict[str, np.ndarray | None] = {}

    def lookup(self, token: str) -> np.ndarray | None:
        """Return unit-normalised vector, or None if unrepresentable."""
        if token in self._cache:
            return self._cache[token]

        vec = self._vecs.get(token)

        if vec is None:
            parts = token.split("_")
            if len(parts) > 1:
                if self._composition == "idf_mean" and self._token_idf:
                    pairs = [
                        (self._vecs[p], self._token_idf.get(p, 1.0))
                        for p in parts if p in self._vecs
                    ]
                    if pairs:
                        vecs_arr = np.array([v for v, _ in pairs])
                        weights  = np.array([w for _, w in pairs])
                        vec = np.average(vecs_arr, weights=weights, axis=0)
                else:
                    component_vecs = [self._vecs[p] for p in parts if p in self._vecs]
                    if component_vecs:
                        vec = np.mean(component_vecs, axis=0)

        result = _unit(vec) if vec is not None else None
        self._cache[token] = result
        return result


def _unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    return v / norm if norm > 1e-9 else v


# ── Spell corrector ────────────────────────────────────────────────────────────

class SpellCorrector:
    """
    Query-time spell correction using pyspellchecker's English dictionary.

    Only fires when a query token has no embedding in the vector store — so
    correctly-spelled words (even unusual ones like "guanciale") are never
    touched. A correction is only accepted when the suggested word itself has
    a vector; this rejects cases where the library guesses a wrong English word
    that happens not to appear in ConceptNet.

    Short tokens (< 4 chars) are skipped to avoid mangling abbreviations.

    Install: pip install pyspellchecker
    """

    def __init__(self) -> None:
        from spellchecker import SpellChecker
        self._checker = SpellChecker()

    def correct(self, word: str) -> str | None:
        """Return a corrected form if one is found, else None."""
        if len(word) < 4:
            return None
        corrected = self._checker.correction(word)
        return corrected if corrected and corrected != word else None


# ── Contextual encoders (BERT-based) ──────────────────────────────────────────

class SpacyBertEncoder:
    """
    Segments text using spaCy noun chunks, then produces a BERT contextual
    vector for each segment within the full sentence context.
    Based on research/experiment/contextual-word-vec.py.

    Unlike static ConceptNet vectors, the vector for "oyster" in
    "beef in oyster sauce" differs from "oyster" in "grilled oysters"
    because BERT reads the whole sentence.

    Swap points:
      bert_model_name — any HuggingFace model with last_hidden_state output
      spacy_model     — any spaCy model with noun_chunks support
    """

    def __init__(
        self,
        bert_model_name: str = "bert-base-uncased",
        spacy_model: str = "en_core_web_sm",
    ):
        import spacy
        import torch
        from transformers import AutoModel, AutoTokenizer
        self._torch = torch
        self._nlp = spacy.load(spacy_model)
        self._bert_tok = AutoTokenizer.from_pretrained(bert_model_name)
        self._bert_mod = AutoModel.from_pretrained(bert_model_name)
        self._bert_mod.eval()

    def encode(self, text: str) -> tuple[list[str], np.ndarray]:
        """
        Returns (segments, unit-normalised matrix of shape (n, 768)).
        Each segment is a spaCy noun chunk or single word; its vector is the
        mean of BERT subword hidden states for that span in context.
        """
        torch = self._torch

        doc = self._nlp(text)
        with doc.retokenize() as retokenizer:
            for chunk in doc.noun_chunks:
                if len(chunk) > 1 or chunk.root.dep_ != "nsubj":
                    retokenizer.merge(chunk)
        segments = [tok.text for tok in doc]

        inputs = self._bert_tok(text, return_tensors="pt")
        with torch.no_grad():
            hidden = self._bert_mod(**inputs).last_hidden_state[0]
        bert_toks = self._bert_tok.convert_ids_to_tokens(inputs["input_ids"][0])

        valid_segs: list[str] = []
        vecs: list[np.ndarray] = []
        for seg in segments:
            subtoks = self._bert_tok.tokenize(seg)
            if not subtoks:
                continue
            start = None
            for i in range(len(bert_toks) - len(subtoks) + 1):
                if bert_toks[i : i + len(subtoks)] == subtoks:
                    start = i
                    break
            if start is None:
                continue
            vec = hidden[start : start + len(subtoks)].mean(dim=0).numpy()
            norm = float(np.linalg.norm(vec))
            if norm > 1e-9:
                valid_segs.append(seg.lower())
                vecs.append(vec / norm)

        if not vecs:
            return [], np.zeros((0, 768), dtype=np.float32)
        return valid_segs, np.stack(vecs).astype(np.float32)


class BertSubwordEncoder:
    """
    Tokenises text with BERT's WordPiece tokeniser and produces a contextual
    BERT vector for each word (subword vectors are averaged back into words).
    Based on research/experiment/bertvector.py.

    Swap point:
      bert_model_name — any HuggingFace model with last_hidden_state output
    """

    def __init__(self, bert_model_name: str = "bert-base-uncased"):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self._torch = torch
        self._bert_tok = AutoTokenizer.from_pretrained(bert_model_name)
        self._bert_mod = AutoModel.from_pretrained(bert_model_name)
        self._bert_mod.eval()

    def encode(self, text: str) -> tuple[list[str], np.ndarray]:
        """
        Returns (words, unit-normalised matrix of shape (n, 768)).
        Multi-subword words (e.g. "toast" + "##ed") have their subword
        vectors averaged into one vector.
        """
        torch = self._torch

        inputs = self._bert_tok(text, return_tensors="pt")
        with torch.no_grad():
            hidden = self._bert_mod(**inputs).last_hidden_state[0]
        toks = self._bert_tok.convert_ids_to_tokens(inputs["input_ids"][0])

        words: list[str] = []
        vecs: list[np.ndarray] = []
        cur_word = ""
        cur_vecs: list = []

        for tok, vec in zip(toks[1:-1], hidden[1:-1]):   # skip [CLS], [SEP]
            if tok.startswith("##"):
                cur_word += tok[2:]
                cur_vecs.append(vec)
            else:
                if cur_word:
                    avg = torch.stack(cur_vecs).mean(dim=0).numpy()
                    norm = float(np.linalg.norm(avg))
                    if norm > 1e-9:
                        words.append(cur_word)
                        vecs.append(avg / norm)
                cur_word = tok
                cur_vecs = [vec]

        if cur_word:   # flush last word
            avg = torch.stack(cur_vecs).mean(dim=0).numpy()
            norm = float(np.linalg.norm(avg))
            if norm > 1e-9:
                words.append(cur_word)
                vecs.append(avg / norm)

        if not vecs:
            return [], np.zeros((0, 768), dtype=np.float32)
        return words, np.stack(vecs).astype(np.float32)


# ── ConceptNet loader ──────────────────────────────────────────────────────────

def load_conceptnet(path: str | Path) -> tuple[dict[str, np.ndarray], set[str]]:
    """
    Load ConceptNet Numberbatch (English mini) vectors.

    Returns:
      raw_vectors  — {token: np.ndarray}  underscore-joined keys for phrases
      phrase_vocab — set of space-separated phrases extracted from multi-word
                     entries; pass directly as PhraseTokenizer.phrase_vocab

    To use a different model instead:
      - GloVe:   parse the same "token float float …" format, pass an empty
                 set for phrase_vocab (or build it from another source).
      - FastText: same text format; no underscore phrase entries.
      - Word2Vec Google News phrases: use gensim.models.KeyedVectors.load_word2vec_format(),
                 extract underscore entries for phrase_vocab.
    """
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    raw_vectors: dict[str, np.ndarray] = {}
    phrase_vocab: set[str] = set()

    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip().split(" ")
            if len(parts) < 2:
                continue
            token = parts[0]
            # Skip header line of the form "N DIM"
            if len(parts) == 2 and token.isdigit():
                continue
            try:
                vec = np.array(parts[1:], dtype=np.float32)
            except ValueError:
                continue
            raw_vectors[token] = vec
            if "_" in token:
                phrase_vocab.add(token.replace("_", " "))

    return raw_vectors, phrase_vocab


# ── Index builder ──────────────────────────────────────────────────────────────

# Fields included in each item's text for indexing:
# item name, description, category, menu_type, and dietary annotations
# (matching the representation used in hybrid, crossencoder, colbert, and sbert search).
def _item_text(item: dict) -> str:
    return " ".join(filter(None, [
        item.get("name", ""),
        item.get("description", ""),
        item.get("category", ""),
        item.get("menu_type", ""),
        item.get("dietary", ""),
    ]))


item_text = _item_text


def build_index(
    menus: dict,
    tokenizer: PhraseTokenizer,
    vector_store: VectorStore,
) -> tuple[dict[str, list[dict]], dict[str, float], float]:
    """
    Phrase-tokenise every menu item and pre-compute unit-normalised vectors.

    Returns:
      index   — {restaurant_id: [entry, …]} where each entry holds the item,
                its phrase tokens, and a stacked matrix of token vectors.
      idf     — {token: float} BM25-style IDF over the phrase-tokenised corpus.
      avgdl   — average token count per item (for BM25 length normalisation).
    """
    index: dict[str, list[dict]] = {}
    doc_freq: dict[str, int] = {}
    total_items = 0
    total_tokens = 0

    for rid, items in menus.items():
        entries: list[dict] = []
        for item in items:
            tokens = tokenizer.tokenize(_item_text(item))
            vecs = [vector_store.lookup(t) for t in tokens]
            # keep only tokens that have representable vectors
            pairs = [(t, v) for t, v in zip(tokens, vecs) if v is not None]
            for t in {t for t, _ in pairs}:
                doc_freq[t] = doc_freq.get(t, 0) + 1
            vecs_matrix = (
                np.stack([v for _, v in pairs]) if pairs
                else np.zeros((0, 1), dtype=np.float32)
            )
            entries.append({
                "item":   item,
                "tokens": [t for t, _ in pairs],
                "vecs":   vecs_matrix,    # shape (n_tokens, dim)
            })
            total_tokens += len(pairs)
            total_items  += 1
        index[rid] = entries

    idf = {
        t: math.log((total_items - df + 0.5) / (df + 0.5) + 1)
        for t, df in doc_freq.items()
    }
    avgdl = total_tokens / max(total_items, 1)
    return index, idf, avgdl


# ── Scoring ────────────────────────────────────────────────────────────────────

_DEFAULT_IDF = 5.0   # IDF for query tokens absent from the indexed corpus


def _soft_tf(query_vec: np.ndarray, item_vecs: np.ndarray, threshold: float) -> float:
    """
    Max cosine similarity of query_vec against all item token vectors.

    threshold is a hard minimum: tokens whose cosine similarity is below it are
    ignored entirely. Returns the raw cosine of the best match (not cosine minus
    threshold), so the score reflects actual similarity strength.

    item_vecs rows and query_vec are already unit-normalised, so cosine
    similarity reduces to a dot product. The result is clamped to [0, 1] to
    guard against float32 rounding (a vector dotted with itself can give
    0.9999998 rather than exactly 1.0).
    """
    if item_vecs.shape[0] == 0:
        return 0.0
    sims = item_vecs @ query_vec                    # (n_tokens,)
    max_sim = min(1.0, float(sims.max()))           # clamp for float32 precision
    return max_sim if max_sim >= threshold else 0.0


def _score_item(
    query_tokens: list[str],
    query_vecs: list[np.ndarray | None],
    entry: dict,
    idf: dict[str, float],
    avgdl: float,
    threshold: float,
    k1: float,
    b: float,
    combiner: str = "bm25",
) -> float:
    """
    Score one item against all query tokens, then combine per-term scores.

    combiner options
    ----------------
    "bm25"    IDF-weighted sum of BM25-saturated soft-TF values (default).
              Partial matches score positively — OR semantics across terms.

    "plus"    Plain sum of raw soft-TF values, no IDF weighting or saturation.
              Also OR semantics, simpler than bm25. Score = Σ soft_tf(q, D).

    "product" Multiply raw soft-TF values across all query terms.
              Any term with soft-TF = 0 collapses the whole score to 0,
              enforcing AND semantics: every query concept must find a match.
              Useful for multi-concept queries like "pasta seafood".

    "min"     Take the minimum soft-TF across all query terms.
              Also AND semantics; the score reflects the weakest match.
              Similar to product but less sensitive to the exact magnitude
              of strong matches.
    """
    item_vecs = entry["vecs"]
    dl = max(len(entry["tokens"]), 1)

    term_scores: list[float] = []
    for qt, qv in zip(query_tokens, query_vecs):
        if qv is None:
            continue
        stf = _soft_tf(qv, item_vecs, threshold)
        if combiner == "bm25":
            if stf == 0.0:
                continue
            tf_norm = stf * (k1 + 1) / (stf + k1 * (1 - b + b * dl / avgdl))
            term_scores.append(idf.get(qt, _DEFAULT_IDF) * tf_norm)
        else:
            term_scores.append(stf)

    if not term_scores:
        return 0.0

    if combiner == "bm25":
        return sum(term_scores)
    if combiner == "plus":
        return sum(term_scores)           # raw soft-TF sum, no IDF/saturation
    if combiner == "product":
        result = 1.0
        for s in term_scores:
            if s == 0.0:
                return 0.0
            result *= s
        return result
    if combiner == "min":
        return min(term_scores) if all(s > 0.0 for s in term_scores) else 0.0
    raise ValueError(f"Unknown combiner: {combiner!r}. Choose bm25, plus, product, or min.")


# ── Query token resolution ────────────────────────────────────────────────────

def resolve_query_tokens(
    query: str,
    tokenizer: PhraseTokenizer,
    vector_store: VectorStore,
    spell_corrector: SpellCorrector | None = None,
) -> tuple[list[str], list[np.ndarray | None], dict[str, str]]:
    """
    Tokenise a query with FMM, resolve each token to a vector, and optionally
    apply spell correction for tokens that have no embedding.

    Returns:
      tokens      — effective token strings (possibly corrected)
      vecs        — unit-normalised vectors, None for tokens with no embedding
      corrections — {original_token: corrected_token} for any corrections made
    """
    raw_tokens = tokenizer.tokenize(query)
    tokens: list[str] = []
    vecs:   list[np.ndarray | None] = []
    corrections: dict[str, str] = {}

    for t in raw_tokens:
        vec = vector_store.lookup(t)
        if vec is None and spell_corrector is not None:
            suggestion = spell_corrector.correct(t)
            if suggestion is not None:
                vec2 = vector_store.lookup(suggestion)
                if vec2 is not None:
                    corrections[t] = suggestion
                    tokens.append(suggestion)
                    vecs.append(vec2)
                    continue
        tokens.append(t)
        vecs.append(vec)

    return tokens, vecs, corrections


# ── Public search function ─────────────────────────────────────────────────────

def search(
    query: str,
    restaurants: dict,
    index: dict[str, list[dict]],
    idf: dict[str, float],
    tokenizer: PhraseTokenizer,
    vector_store: VectorStore,
    avgdl: float,
    similarity_threshold: float = 0.5,
    k1: float = 2.0,
    b: float = 0.0,
    combiner: str = "bm25",
    spell_corrector: SpellCorrector | None = None,
    out_corrections: dict[str, str] | None = None,
) -> list[dict]:
    """
    Search all indexed items for query, returning results sorted by score.

    combiner controls how per-term scores are combined; see _score_item.

    spell_corrector: optional SpellCorrector; when a query token has no vector,
        its correction is tried. Only accepted if the corrected word also has a
        vector. Pass out_corrections={} to receive a {original: corrected} map.

    To integrate with evaluate.py, build a wrapper:
        def search_fn(query, restaurants, menus):
            return search(query, restaurants, index, idf, tokenizer,
                          vector_store, avgdl, combiner=combiner)
    """
    query_tokens, query_vecs, corrections = resolve_query_tokens(
        query, tokenizer, vector_store, spell_corrector
    )
    if out_corrections is not None:
        out_corrections.update(corrections)

    scored: list[tuple[float, dict]] = []
    for rid, entries in index.items():
        restaurant_name = restaurants[rid].get("name", rid)
        for entry in entries:
            s = _score_item(
                query_tokens, query_vecs, entry, idf, avgdl,
                similarity_threshold, k1, b, combiner,
            )
            if s > 0:
                item = entry["item"]
                scored.append((s, {
                    "restaurant": restaurant_name,
                    "item":       item["name"],
                    "description": item["description"],
                    "price":      item["price"],
                    "price_raw":  item["price_raw"],
                    "category":   item["category"],
                    "menu_type":  item["menu_type"],
                    "dietary":    item.get("dietary", ""),
                    "score":      round(s, 4),
                    "tokens":     entry["tokens"],   # for debugging phrase detection
                }))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [r for _, r in scored]


# ── Contextual index / search (for SpacyBertEncoder / BertSubwordEncoder) ─────

def build_index_contextual(
    menus: dict,
    encoder,
) -> tuple[dict[str, list[dict]], dict[str, float], float]:
    """
    Like build_index but runs a contextual BERT encoder over each item instead
    of using PhraseTokenizer + VectorStore. Each item is encoded once at index
    time; the resulting per-token vectors are contextual (depend on the full
    item text).
    """
    index: dict[str, list[dict]] = {}
    doc_freq: dict[str, int] = {}
    total_items = 0
    total_tokens = 0

    all_rids = list(menus.keys())
    for n, rid in enumerate(all_rids, 1):
        if n % 50 == 0 or n == len(all_rids):
            print(f"\r  {n}/{len(all_rids)} restaurants", end="", flush=True)
        entries: list[dict] = []
        for item in menus[rid]:
            segments, vecs_matrix = encoder.encode(_item_text(item))
            for t in set(segments):
                doc_freq[t] = doc_freq.get(t, 0) + 1
            entries.append({"item": item, "tokens": segments, "vecs": vecs_matrix})
            total_tokens += len(segments)
            total_items  += 1
        index[rid] = entries
    print()

    idf = {
        t: math.log((total_items - df + 0.5) / (df + 0.5) + 1)
        for t, df in doc_freq.items()
    }
    return index, idf, total_tokens / max(total_items, 1)


def search_contextual(
    query: str,
    restaurants: dict,
    index: dict[str, list[dict]],
    idf: dict[str, float],
    encoder,
    avgdl: float,
    similarity_threshold: float = 0.5,
    k1: float = 2.0,
    b: float = 0.0,
    combiner: str = "bm25",
) -> list[dict]:
    """
    Like search() but derives query vectors by running the contextual encoder
    on the query string (so query-word vectors are also context-aware).
    """
    query_tokens, qvecs_matrix = encoder.encode(query)
    query_vecs: list[np.ndarray | None] = list(qvecs_matrix) if len(qvecs_matrix) else []

    scored: list[tuple[float, dict]] = []
    for rid, entries in index.items():
        restaurant_name = restaurants[rid].get("name", rid)
        for entry in entries:
            s = _score_item(
                query_tokens, query_vecs, entry, idf, avgdl,
                similarity_threshold, k1, b, combiner,
            )
            if s > 0:
                item = entry["item"]
                scored.append((s, {
                    "restaurant":  restaurant_name,
                    "item":        item["name"],
                    "description": item["description"],
                    "price":       item["price"],
                    "price_raw":   item["price_raw"],
                    "category":    item["category"],
                    "menu_type":   item["menu_type"],
                    "dietary":     item.get("dietary", ""),
                    "score":       round(s, 4),
                    "tokens":      entry["tokens"],
                }))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [r for _, r in scored]


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phrase-aware Soft-BM25 menu search (Approach 3.5)",
        parents=[cli_args(), restaurant_scope_cli_args()],
    )
    parser.add_argument(
        "--show-tokens", action="store_true",
        help="Print phrase tokens for each result (useful for debugging)",
    )
    parser.add_argument("terms", nargs="+", help="Query words")
    args = parser.parse_args()

    print("Loading menus…", end=" ", flush=True)
    restaurants, menus = load_data(judged_restaurant_ids() if args.benchmark_only else None)
    print(f"{sum(len(v) for v in menus.values())} items"
          + (" (benchmark subset)" if args.benchmark_only else ""))

    query = " ".join(args.terms)

    if args.segmenter == "fmm":
        if not args.vectors:
            parser.error("--vectors PATH is required for --segmenter fmm")
        print("Loading vectors…", end=" ", flush=True)
        raw_vectors, phrase_vocab = load_conceptnet(args.vectors)
        print(f"{len(raw_vectors):,} entries, {len(phrase_vocab):,} phrase vocab entries")
        tokenizer    = PhraseTokenizer(phrase_vocab, max_phrase_len=args.max_phrase_len)
        vector_store = VectorStore(raw_vectors, composition=args.composition)
        print("Building index…", end=" ", flush=True)
        index, idf, avgdl = build_index(menus, tokenizer, vector_store)
        print(f"{sum(len(v) for v in index.values())} items, avgdl={avgdl:.1f}")
        corrector = SpellCorrector() if args.spell_correct else None
        query_tokens, _, corrections = resolve_query_tokens(
            query, tokenizer, vector_store, corrector
        )
        print(f"\nQuery : '{query}'")
        print(f"Tokens: {query_tokens}")
        if corrections:
            print("Spell corrections: " +
                  ", ".join(f"{o} → {c}" for o, c in corrections.items()))
        print()
        results = search(
            query, restaurants, index, idf, tokenizer, vector_store, avgdl,
            similarity_threshold=args.threshold,
            k1=args.k1,
            b=args.b,
            combiner=args.combiner,
            spell_corrector=corrector,
        )
    else:
        print(f"Loading BERT encoder ({args.segmenter})…", flush=True)
        encoder = (
            SpacyBertEncoder() if args.segmenter == "spacy_bert"
            else BertSubwordEncoder()
        )
        print("Building index…")
        index, idf, avgdl = build_index_contextual(menus, encoder)
        print(f"  avgdl={avgdl:.1f} tokens")
        query_tokens, query_vecs = encoder.encode(query)
        print(f"\nQuery : '{query}'")
        print(f"Tokens: {query_tokens}\n")
        results = search_contextual(
            query, restaurants, index, idf, encoder, avgdl,
            similarity_threshold=args.threshold,
            k1=args.k1,
            b=args.b,
            combiner=args.combiner,
        )

    if not results:
        print("No results.")
    for r in results[:20]:
        price_str = (
            f"${r['price']:.2f}" if r["price"] is not None
            else r["price_raw"] or "N/A"
        )
        dietary_str = f" ({r['dietary']})" if r.get("dietary") else ""
        print(f"  [{r['score']:.4f}] {r['restaurant']} | {r['item']}  {price_str}"
              f"  [{r['category']} · {r['menu_type']}]{dietary_str}")
        if args.show_tokens:
            print(f"           item tokens: {r['tokens']}")
        if r["description"]:
            print(f"           {r['description']}")
        print()
