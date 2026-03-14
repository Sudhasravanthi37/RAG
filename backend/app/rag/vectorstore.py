"""
vectorstore.py — FAISS store using IndexFlatIP (cosine similarity).

Fixes vs original:
- IndexFlatL2  →  IndexFlatIP  (inner product == cosine on normalized vecs)
- Relevance scores are now real cosine similarities (0–1), not normalised L2
- _normalize() applied before add() and search() for safety
- All other methods (save/load/exists/get_metrics) unchanged
"""
import faiss, pickle, os, time
import numpy as np

EMBEDDING_DIM = 384


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (vecs / norms).astype("float32")


class VectorStore:
    def __init__(self, dim: int = EMBEDDING_DIM, store_path: str = "data/default_store"):
        self.dim = dim
        self.store_path = store_path
        self.index = faiss.IndexFlatIP(dim)   # cosine similarity (vectors are L2-normalised)
        self.texts: list[str] = []
        self.full_text: str = ""
        self._last_metrics: dict = {}

    def exists(self) -> bool:
        return os.path.exists(os.path.join(self.store_path, "index.faiss"))

    def save(self):
        os.makedirs(self.store_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(self.store_path, "index.faiss"))
        with open(os.path.join(self.store_path, "texts.pkl"), "wb") as f:
            pickle.dump(self.texts, f)
        with open(os.path.join(self.store_path, "full_text.pkl"), "wb") as f:
            pickle.dump(self.full_text, f)

    def load(self):
        self.index = faiss.read_index(os.path.join(self.store_path, "index.faiss"))
        with open(os.path.join(self.store_path, "texts.pkl"), "rb") as f:
            self.texts = pickle.load(f)
        full_path = os.path.join(self.store_path, "full_text.pkl")
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                self.full_text = pickle.load(f)

    def add(self, embeddings: np.ndarray, texts: list[str]):
        if not len(texts):
            return
        arr = _normalize(np.array(embeddings).astype("float32"))
        self.index.add(arr)
        self.texts.extend(texts)
        self.full_text += "\n".join(texts) + "\n"

    def search(self, query_embedding: np.ndarray, k: int = 6) -> list[str]:
        t0 = time.perf_counter()
        if not self.texts:
            return []
        k = min(k, len(self.texts))
        q = _normalize(np.array(query_embedding).astype("float32").reshape(1, -1))
        scores_raw, indices = self.index.search(q, k)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        valid = [
            (int(i), float(s))
            for i, s in zip(indices[0], scores_raw[0])
            if 0 <= int(i) < len(self.texts)
        ]
        # Cosine scores in [-1,1]; clip to [0,1]
        # Only keep chunks with score >= 0.20; fall back to top-3 if none pass
        filtered = [(i, max(0.0, s)) for i, s in valid if s >= 0.20]
        if not filtered:
            filtered = [(i, max(0.0, s)) for i, s in valid[:3]]

        chunks = [self.texts[i] for i, _ in filtered]
        scores = [round(s, 4) for _, s in filtered]
        avg    = round(sum(scores) / len(scores), 4) if scores else 0.0

        self._last_metrics = {
            "latency_ms": latency_ms,
            "chunks_retrieved": len(chunks),
            "total_chunks_in_store": len(self.texts),
            "relevance_scores": scores,
            "avg_relevance_score": avg,
        }
        return chunks

    def get_metrics(self) -> dict:
        return self._last_metrics
