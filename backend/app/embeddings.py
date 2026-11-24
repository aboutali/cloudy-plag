"""Sentence embeddings for paraphrase detection.

Model: paraphrase-multilingual-MiniLM-L12-v2 (384-dim, ~120MB).
Loaded lazily on first use; cached for the process lifetime.

The model is good enough as a *lead generator*. Findings produced by
embedding similarity are tagged `paraphrase` and require two reviewer
confirmations before publication (see docs/evidence-model.md).
"""
from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

import numpy as np

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def embed(texts: Sequence[str]) -> np.ndarray:
    """Return L2-normalized embeddings (cosine == dot product)."""
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
    vecs = _model().encode(
        list(texts),
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vecs.astype(np.float32)
