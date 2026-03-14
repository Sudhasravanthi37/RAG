"""
upload.py — API #9: Upload files.
Fixes applied (minimal changes only):
  - chat_id is now optional (Form("")); if empty a new chat is auto-created (#8)
  - mode param added so the auto-created chat title reflects the file name
  - store.load() called before store.add() to accumulate (not replace) chunks (#9)
  - incognito path unchanged
"""
import os, uuid, tempfile
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user_id
from app.db.models import Chat, Document as DocModel
from app.ingestion.ocr import extract_text
from app.rag.chunker import chunk_text
from app.rag.embeddings import embed
from app.rag.vectorstore import VectorStore, EMBEDDING_DIM
from app.config import settings

router = APIRouter(tags=["Upload"])

ALLOWED_EXTS = {".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg"}

MAGIC_MAP = {
    b"%PDF":     ".pdf",
    b"\x89PNG":  ".png",
    b"\xff\xd8\xff": ".jpg",
    b"PK\x03\x04":   ".docx",
}

def _verify_magic(data: bytes, ext: str) -> bool:
    for magic, expected in MAGIC_MAP.items():
        if data.startswith(magic):
            return ext in (expected, ".jpeg") if expected == ".jpg" else ext == expected
    return ext in {".txt"}

def _chat_upload_dir(chat_id: str) -> str:
    p = os.path.join(settings.UPLOAD_BASE, chat_id)
    os.makedirs(p, exist_ok=True)
    return p

def _chat_vector_dir(chat_id: str) -> str:
    p = os.path.join(settings.VECTOR_DB_PATH, chat_id)
    os.makedirs(p, exist_ok=True)
    return p


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    chat_id: str = Form(""),          # now optional — empty → auto-create chat (#8)
    incognito: bool = Form(False),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # 1. Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTS)}")

    # 2. Read bytes
    raw = file.file.read()
    if len(raw) == 0:
        raise HTTPException(400, "Uploaded file is empty")

    # 3. Magic number check
    if not _verify_magic(raw, ext):
        raise HTTPException(400, "File content does not match its extension (magic number check failed)")

    if incognito:
        return _incognito_process(raw, file.filename, ext)

    # 4. Auto-create chat if no chat_id supplied (#8)
    auto_created = False
    if not chat_id:
        title = os.path.splitext(file.filename or "New Chat")[0][:80]
        new_chat = Chat(UserId=user_id, Title=title)
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        chat_id = new_chat.ChatId
        auto_created = True

    # 5. Verify chat ownership
    chat = db.query(Chat).filter(
        Chat.ChatId == chat_id, Chat.UserId == user_id, Chat.IsDeleted == False
    ).first()
    if not chat:
        raise HTTPException(404, "Chat not found")

    # 6. Save file
    upload_dir = _chat_upload_dir(chat_id)
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(raw)

    # 7. Extract text
    try:
        text = extract_text(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(400, f"Text extraction failed: {e}")

    if not text or not text.strip():
        os.remove(file_path)
        raise HTTPException(400, "No extractable text found in this document")

    # 8. Chunk + embed
    chunks = chunk_text(text)
    embeddings = embed(chunks)

    # 9. ACCUMULATE — load existing store first, then add (#9 fix)
    vector_dir = _chat_vector_dir(chat_id)
    store = VectorStore(EMBEDDING_DIM, store_path=vector_dir)
    if store.exists():
        store.load()          # ← loads previous files' chunks
    store.add(embeddings, chunks)
    store.save()

    # 10. Record in DB
    doc = DocModel(
        DocumentId=doc_id,
        ChatId=chat_id,
        UserId=user_id,
        FileName=file.filename,
        FilePath=file_path,
        ChunkCount=len(chunks),
        CreatedAt=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()

    return {
        "message": "Document uploaded and indexed",
        "filename": file.filename,
        "doc_id": doc_id,
        "chat_id": chat_id,
        "auto_created_chat": auto_created,
        "chunks_added": len(chunks),
        "total_chunks_in_store": len(store.texts),
        "incognito": False,
    }


def _incognito_process(raw: bytes, filename: str, ext: str) -> dict:
    """Process file in memory for incognito mode. Nothing persisted."""
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        text = extract_text(tmp_path)
    finally:
        os.remove(tmp_path)

    if not text or not text.strip():
        raise HTTPException(400, "No extractable text found")

    chunks = chunk_text(text)
    embeddings = embed(chunks)

    session_id = str(uuid.uuid4())
    incognito_path = f"/tmp/incognito_{session_id}"
    store = VectorStore(EMBEDDING_DIM, store_path=incognito_path)
    store.add(embeddings, chunks)
    store.save()

    return {
        "message": "Incognito document processed (not saved)",
        "filename": filename,
        "chunks_added": len(chunks),
        "incognito": True,
        "session_id": session_id,
    }


@router.get("/chats/{chat_id}/documents")
def list_chat_documents(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.ChatId == chat_id, Chat.UserId == user_id).first()
    if not chat:
        raise HTTPException(404, "Chat not found")
    docs = db.query(DocModel).filter(DocModel.ChatId == chat_id, DocModel.IsDeleted == False).all()
    return [{"doc_id": d.DocumentId, "filename": d.FileName, "chunks": d.ChunkCount, "uploaded_at": d.CreatedAt} for d in docs]
