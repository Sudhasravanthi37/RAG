"""
chunker.py — Sentence-aware sliding-window chunker.
Replaces the naive character-split that caused ~8% retrieval relevance.
Only this function is changed; all callers remain identical.
"""
import re


def chunk_text(text: str, max_chars: int = 600, overlap_chars: int = 150, min_chars: int = 60) -> list[str]:
    """
    Split text into overlapping chunks that respect sentence boundaries.

    Changes vs original:
    - Sentence-aware: never cuts mid-sentence
    - Sliding overlap: last N chars of each chunk carried into next
    - Smaller max (600 vs 800): sharper, more focused embeddings
    - Paragraph-first split: preserves document structure
    """
    if not text or not text.strip():
        return []

    # Split on blank lines first to respect paragraph structure
    paragraphs = re.split(r'\n{2,}', text)
    sentences: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Split on sentence-ending punctuation followed by whitespace + capital
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', re.sub(r'\s+', ' ', para))
        sentences.extend([p.strip() for p in parts if p.strip()])
        sentences.append('')   # paragraph boundary marker

    chunks: list[str] = []
    current: list[str] = []
    cur_len = 0

    for sent in sentences:
        # Paragraph boundary — flush
        if sent == '':
            if current:
                val = ' '.join(current).strip()
                if len(val) >= min_chars:
                    chunks.append(val)
                elif chunks:
                    chunks[-1] += ' ' + val
                current = []
                cur_len = 0
            continue

        slen = len(sent)
        if cur_len + slen > max_chars and current:
            val = ' '.join(current).strip()
            if len(val) >= min_chars:
                chunks.append(val)
            # Carry overlap sentences into next chunk
            overlap: list[str] = []
            olen = 0
            for s in reversed(current):
                if olen + len(s) <= overlap_chars:
                    overlap.insert(0, s)
                    olen += len(s)
                else:
                    break
            current = overlap
            cur_len = olen

        current.append(sent)
        cur_len += slen

    # Flush remaining
    if current:
        val = ' '.join(current).strip()
        if len(val) >= min_chars:
            chunks.append(val)
        elif chunks:
            chunks[-1] += ' ' + val

    # Deduplicate exact copies
    seen: set = set()
    out: list[str] = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out
