from app.rag.embeddings import embed

def retrieve(query: str, store, k: int = 4) -> list[str]:
    if not store or not store.texts:
        return []
    q_emb = embed([query])
    return store.search(q_emb, k=k)
