"""
embeddings.py — L2-normalized embeddings for cosine similarity.
Only change: normalize_embeddings=True so FAISS inner-product == cosine.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def embed(texts: list[str]) -> np.ndarray:
    """Encode and L2-normalize so inner-product search equals cosine similarity."""
    if not texts:
        return np.array([])
    return _get_model().encode(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,   # ← key fix: cosine similarity
        batch_size=32,
    ).astype("float32")
