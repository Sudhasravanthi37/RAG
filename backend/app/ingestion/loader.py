import os
from app.ingestion.ocr import extract_text

def load_documents(folder: str) -> list[str]:
    texts = []
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        try:
            text = extract_text(path)
            if text and text.strip():
                texts.append(text)
        except Exception as e:
            print(f"[WARN] Skipping {fname}: {e}")
    return texts
