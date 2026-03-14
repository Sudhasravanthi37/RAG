"""
routes.py — All chat + profile APIs:
  5)  POST /chat/new             — New chat + first message, create record in DB with Mode
  6)  POST /chat                 — New message in chat → create MessageId with ChatId as FK
  7)  GET  /modes                — API to get list of modes like "Translator"
  8)  GET  /chats                — Chat history → API to get all chat IDs
  10) POST /chat                 — Send message → API to call LLM
  11) PATCH /chats/{id}/datetime — Update datetime in chat ID
  12) DELETE /chats/{id}         — Delete chat and its docs if not used in any other chat
  14) PATCH /profile/username    — Change username
  15) POST  /profile/picture     — Change profile pic
  16) PATCH /profile/password    — Change password (item 16 from notes)
"""
import re, os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_id, get_db
from app.rag.prompts import PROMPTS, MEDICAL_AUTO_QUERY
from app.llm.groq_client import generate
from app.rag.retriever import retrieve
from app.rag.vectorstore import VectorStore, EMBEDDING_DIM
from app.db.models import Chat, ChatMessage, Mode, User, Document as DocModel
from app.core.security import hash_password, verify_password
from app.config import settings

router = APIRouter(tags=["Chat"])

VECTOR_BASE = settings.VECTOR_DB_PATH
STATIC_VECTOR_BASE = settings.STATIC_VECTOR_DB_PATH


# ══ SCHEMAS ════════════════════════════════════════════════════════════════
class NewChatRequest(BaseModel):
    title: str = "New Chat"
    mode: str = "qa"
    first_message: str = ""     # API #5: New chat + first message together

class MessageRequest(BaseModel):
    chat_id: str
    mode: str
    query: str = ""
    incognito: bool = False
    incognito_session_id: str = ""

class UpdateTitleRequest(BaseModel):
    title: str

class ChangeUsernameRequest(BaseModel):
    new_name: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ══ HELPERS ════════════════════════════════════════════════════════════════
def _mode_id(db: Session, mode_name: str) -> int:
    m = db.query(Mode).filter(Mode.ModeName == mode_name).first()
    if not m:
        raise HTTPException(400, f"Unknown mode: {mode_name}")
    return m.ModeId

def _load_store(chat_id: str) -> VectorStore:
    path = os.path.join(VECTOR_BASE, chat_id)
    store = VectorStore(EMBEDDING_DIM, store_path=path)
    if store.exists():
        store.load()
    return store

def _load_static_store(mode: str) -> VectorStore | None:
    path = os.path.join(STATIC_VECTOR_BASE, mode)
    store = VectorStore(EMBEDDING_DIM, store_path=path)
    if store.exists():
        store.load()
        return store
    return None

def _split(text: str, max_chars: int = 3000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def _extract_paragraph(text: str, n: int) -> str | None:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    return paragraphs[n-1] if 1 <= n <= len(paragraphs) else None


# ══ 7) MODES LIST ══════════════════════════════════════════════════════════
@router.get("/modes")
def list_modes(db: Session = Depends(get_db)):
    """API #7: Get list of all modes like 'Translator'."""
    modes = db.query(Mode).filter(Mode.IsActive == True).all()
    return [
        {
            "mode_id": m.ModeId,
            "mode_name": m.ModeName,
            "display_name": m.DisplayName,
            "icon": m.Icon,
            "supports_text_input": m.SupportsTextInput,
            "auto_process": m.AutoProcess,
            "supports_incognito": True,
        }
        for m in modes
    ]


# ══ 5) NEW CHAT + FIRST MESSAGE ════════════════════════════════════════════
@router.post("/chat/new")
def create_new_chat(
    req: NewChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    API #5: Create new chat + first message together.
    Creates a Chat record in DB along with Mode FK.
    If first_message provided, also creates the first ChatMessage record.
    """
    if req.mode not in PROMPTS:
        raise HTTPException(400, f"Invalid mode: {req.mode}")

    # Create chat
    chat = Chat(UserId=user_id, Title=req.title or "New Chat")
    db.add(chat)
    db.commit()
    db.refresh(chat)

    result = {"chat_id": chat.ChatId, "title": chat.Title}

    # Optionally save first message
    if req.first_message.strip():
        mode_id = _mode_id(db, req.mode)
        db.add(ChatMessage(ChatId=chat.ChatId, ModeId=mode_id, Role="user", Content=req.first_message))
        chat.LastMessageAt = datetime.utcnow()
        db.commit()
        result["first_message_saved"] = True

    return result


# ══ 8) CHAT HISTORY — Get all chat IDs ════════════════════════════════════
@router.get("/chats")
def list_chats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """API #8: Chat history → get all chat IDs for the user."""
    chats = (
        db.query(Chat)
        .filter(Chat.UserId == user_id, Chat.IsDeleted == False)
        .order_by(Chat.LastMessageAt.desc().nullslast(), Chat.CreatedAt.desc())
        .all()
    )
    return [
        {
            "chat_id": c.ChatId,
            "title": c.Title,
            "last_message_at": c.LastMessageAt,
            "created_at": c.CreatedAt,
        }
        for c in chats
    ]


# ══ GET CHAT MESSAGES ══════════════════════════════════════════════════════
@router.get("/chats/{chat_id}/messages")
def get_messages(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.ChatId == chat_id, Chat.UserId == user_id).first()
    if not chat:
        raise HTTPException(404, "Chat not found")
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.ChatId == chat_id, ChatMessage.IsDeleted == False)
        .order_by(ChatMessage.CreatedAt.asc())
        .all()
    )
    return [{"role": m.Role, "content": m.Content, "created_at": m.CreatedAt} for m in msgs]


# ══ 11) UPDATE DATETIME ════════════════════════════════════════════════════
@router.patch("/chats/{chat_id}/datetime")
def update_chat_datetime(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """API #11: Update datetime in chat ID."""
    chat = db.query(Chat).filter(Chat.ChatId == chat_id, Chat.UserId == user_id).first()
    if not chat:
        raise HTTPException(404, "Chat not found")
    chat.LastMessageAt = datetime.utcnow()
    db.commit()
    return {"chat_id": chat_id, "last_message_at": chat.LastMessageAt}


# ══ PATCH CHAT TITLE ═══════════════════════════════════════════════════════
@router.patch("/chats/{chat_id}/title")
def update_title(
    chat_id: str,
    body: UpdateTitleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.ChatId == chat_id, Chat.UserId == user_id).first()
    if not chat:
        raise HTTPException(404, "Chat not found")
    chat.Title = body.title
    chat.UpdatedAt = datetime.utcnow()
    db.commit()
    return {"message": "Title updated"}


# ══ 12) DELETE CHAT ════════════════════════════════════════════════════════
@router.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    API #12: Delete chat and its respective documents
    IF they are not used in any other chats.
    """
    chat = db.query(Chat).filter(Chat.ChatId == chat_id, Chat.UserId == user_id).first()
    if not chat:
        raise HTTPException(404, "Chat not found")

    # Soft-delete chat
    chat.IsDeleted = True
    chat.UpdatedAt = datetime.utcnow()

    # Soft-delete documents (only this chat's docs — they are per-chat by design)
    db.query(DocModel).filter(DocModel.ChatId == chat_id).update({"IsDeleted": True})
    db.commit()

    return {"message": "Chat and its documents deleted successfully"}


# ══ 6 + 10) SEND MESSAGE → CALL LLM ═══════════════════════════════════════
@router.post("/chat")
def send_message(
    req: MessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    API #6 + #10:
    - Creates ChatMessage record with ChatId as foreign key (API #6)
    - Calls LLM to generate answer (API #10)
    - Returns answer + retrieval metrics
    """
    if req.mode not in PROMPTS:
        raise HTTPException(400, f"Invalid mode: {req.mode}")

    chat = db.query(Chat).filter(Chat.ChatId == req.chat_id, Chat.UserId == user_id, Chat.IsDeleted == False).first()
    if not chat:
        raise HTTPException(404, "Chat not found")

    mode_id = _mode_id(db, req.mode)

    # ── Load vector store ──
    if req.incognito and req.incognito_session_id:
        store = VectorStore(EMBEDDING_DIM, store_path=f"/tmp/incognito_{req.incognito_session_id}")
        if store.exists():
            store.load()
    else:
        store = _load_store(req.chat_id)

    # ── Static augmentation for medical + resume only (legal uses uploaded docs only) ──
    static_context = ""
    if req.mode in ("medical", "resume"):
        static_store = _load_static_store(req.mode)
        if static_store and req.query.strip():
            try:
                from app.rag.embeddings import embed as _emb
                static_chunks = static_store.search(_emb([req.query or "analyze"]), k=6)
                static_context = "\n\n".join(static_chunks[:4])
            except Exception:
                pass

    # ── Medical auto-query ──
    actual_query = req.query.strip()
    if req.mode == "medical" and not actual_query:
        actual_query = MEDICAL_AUTO_QUERY

    if not actual_query:
        raise HTTPException(400, "Query cannot be empty")

    # ── TRANSLATOR ──
    if req.mode == "translator":
        if not store.full_text:
            raise HTTPException(400, "No document found. Please upload a file first.")
        query_lower = actual_query.lower()
        text_to_translate = store.full_text
        para_match = re.search(r"paragraph\s+(\d+)", query_lower)
        if para_match:
            para = _extract_paragraph(store.full_text, int(para_match.group(1)))
            if not para:
                raise HTTPException(400, "Paragraph not found")
            text_to_translate = para
        elif any(k in query_lower for k in ["summary", "brief", "short"]):
            text_to_translate = generate("Summarize this document briefly:", store.full_text)
        chunks = [generate(PROMPTS["translator"], f"{actual_query}\n\nText:\n{c}") for c in _split(text_to_translate)]
        final_answer = "\n\n".join(chunks)
        retrieval_metrics = {"mode": "full_document"}

    # ── ALL OTHER MODES ──
    else:
        if not store.texts and not static_context:
            raise HTTPException(400, "No document uploaded to this chat yet. Please upload a file first.")

        context_parts = []
        retrieval_metrics = {}

        if store.texts:
            from app.rag.embeddings import embed as _embed
            chunks = retrieve(actual_query, store)
            retrieval_metrics = store.get_metrics()
            if chunks:
                context_parts.append("### Document Context:\n" + "\n\n".join(chunks))

        if static_context:
            context_parts.append("### Reference Knowledge Base:\n" + static_context)

        context = "\n\n".join(context_parts) or "No context available."
        final_answer = generate(PROMPTS[req.mode], f"Context:\n{context}\n\nQuestion:\n{actual_query}")

    # ── Save messages (skip in incognito) ──
    if not req.incognito:
        db.add(ChatMessage(ChatId=req.chat_id, ModeId=mode_id, Role="user", Content=actual_query))
        db.add(ChatMessage(ChatId=req.chat_id, ModeId=mode_id, Role="assistant", Content=final_answer))
        chat.LastMessageAt = datetime.utcnow()
        db.commit()

        # Auto-update title from first real message
        if chat.Title in ("New Chat", "") and actual_query:
            chat.Title = actual_query[:50] + ("..." if len(actual_query) > 50 else "")
            db.commit()

    return {
        "answer": final_answer,
        "incognito": req.incognito,
        "retrieval_metrics": retrieval_metrics,
    }


# ══ RETRIEVAL METRICS ══════════════════════════════════════════════════════
@router.get("/chats/{chat_id}/metrics")
def get_metrics(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    store = _load_store(chat_id)
    docs = db.query(DocModel).filter(DocModel.ChatId == chat_id, DocModel.IsDeleted == False).all()
    return {
        "chat_id": chat_id,
        "total_chunks": len(store.texts) if store.texts else 0,
        "documents_count": len(docs),
        "documents": [{"filename": d.FileName, "chunks": d.ChunkCount} for d in docs],
        "store_ready": store.exists(),
    }


# ══ 14) CHANGE USERNAME ════════════════════════════════════════════════════
@router.patch("/profile/username")
def change_username(
    body: ChangeUsernameRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """API #14: Change username."""
    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.Name = body.new_name
    user.UpdatedAt = datetime.utcnow()
    db.commit()
    return {"message": "Username updated", "new_name": user.Name}


# ══ 15) CHANGE PROFILE PIC ═════════════════════════════════════════════════
@router.post("/profile/picture")
def change_profile_pic(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """API #15: Change profile picture."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(400, "Only JPG, PNG, WEBP allowed")
    os.makedirs(settings.PROFILE_PICS_PATH, exist_ok=True)
    fname = f"{user_id}{ext}"
    fpath = os.path.join(settings.PROFILE_PICS_PATH, fname)
    with open(fpath, "wb") as f:
        f.write(file.file.read())
    pic_url = f"/static/profile_pics/{fname}"
    user = db.query(User).filter(User.UserId == user_id).first()
    user.ProfilePicUrl = pic_url
    user.UpdatedAt = datetime.utcnow()
    db.commit()
    return {"message": "Profile picture updated", "profile_pic_url": pic_url}


# ══ 16) CHANGE PASSWORD ════════════════════════════════════════════════════
@router.patch("/profile/password")
def change_password(
    body: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """API #16: Change password."""
    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if not verify_password(body.current_password, user.PasswordHash):
        raise HTTPException(400, "Current password is incorrect")
    user.PasswordHash = hash_password(body.new_password)
    user.UpdatedAt = datetime.utcnow()
    db.commit()
    return {"message": "Password changed successfully"}


# ══ HEALTH CHECK ═══════════════════════════════════════════════════════════
@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    return {"status": "ok", "database": db_status, "timestamp": datetime.utcnow().isoformat()}
