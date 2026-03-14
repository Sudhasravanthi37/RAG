import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.db.database import Base

# Use String for SQLite compatibility; PostgreSQL uses UUID natively
class User(Base):
    __tablename__ = "users"
    UserId       = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Name         = Column(String(100), nullable=False)
    Email        = Column(String(255), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(512), nullable=False)
    Role         = Column(String(20), default="USER")
    IsActive     = Column(Boolean, default=True)
    IsEmailVerified = Column(Boolean, default=False)
    ProfilePicUrl   = Column(String(500), nullable=True)
    CreatedAt    = Column(DateTime, default=datetime.utcnow)
    UpdatedAt    = Column(DateTime, nullable=True)
    LastLoginAt  = Column(DateTime, nullable=True)

    chats     = relationship("Chat", back_populates="user")
    otps      = relationship("EmailOTP", back_populates="user")
    documents = relationship("Document", back_populates="user")


class EmailOTP(Base):
    __tablename__ = "email_otps"
    Id        = Column(Integer, primary_key=True, autoincrement=True)
    UserId    = Column(String(36), ForeignKey("users.UserId"), nullable=False)
    OtpCode   = Column(String(10), nullable=False)
    OtpType   = Column(String(30), default="EMAIL_VERIFY")  # EMAIL_VERIFY | PASSWORD_RESET | CONFIRM
    IsUsed    = Column(Boolean, default=False)
    ExpiresAt = Column(DateTime, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="otps")


class Mode(Base):
    __tablename__ = "modes"
    ModeId      = Column(Integer, primary_key=True, autoincrement=True)
    ModeName    = Column(String(50), unique=True, nullable=False)
    DisplayName = Column(String(100), nullable=False, default="")
    Icon        = Column(String(50), nullable=True)
    IsActive    = Column(Boolean, default=True)
    SupportsTextInput = Column(Boolean, default=True)
    AutoProcess       = Column(Boolean, default=False)

    messages = relationship("ChatMessage", back_populates="mode")


class Chat(Base):
    __tablename__ = "chats"
    ChatId        = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    UserId        = Column(String(36), ForeignKey("users.UserId"), nullable=False)
    Title         = Column(String(255), default="New Chat")
    Status        = Column(String(20), default="ACTIVE")
    IsDeleted     = Column(Boolean, default=False)
    CreatedAt     = Column(DateTime, default=datetime.utcnow)
    UpdatedAt     = Column(DateTime, nullable=True)
    LastMessageAt = Column(DateTime, nullable=True)

    user      = relationship("User", back_populates="chats")
    messages  = relationship("ChatMessage", back_populates="chat")
    documents = relationship("Document", back_populates="chat")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    MessageId = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ChatId    = Column(String(36), ForeignKey("chats.ChatId"), nullable=False)
    ModeId    = Column(Integer, ForeignKey("modes.ModeId"), nullable=True)
    Role      = Column(String(20), nullable=False)
    Content   = Column(Text, nullable=False)
    IsDeleted = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    mode = relationship("Mode", back_populates="messages")


class Document(Base):
    __tablename__ = "documents"
    DocumentId = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ChatId     = Column(String(36), ForeignKey("chats.ChatId"), nullable=False)
    UserId     = Column(String(36), ForeignKey("users.UserId"), nullable=False)
    FileName   = Column(String(255), nullable=False)
    FilePath   = Column(String(500), nullable=False)
    ChunkCount = Column(Integer, default=0)
    IsDeleted  = Column(Boolean, default=False)
    CreatedAt  = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="documents")
    user = relationship("User", back_populates="documents")


def seed_modes(db_session):
    """Seed default modes on first startup."""
    default_modes = [
        {"ModeName": "qa",             "DisplayName": "Q&A",               "Icon": "💬", "SupportsTextInput": True,  "AutoProcess": False},
        {"ModeName": "translator",     "DisplayName": "Translator",         "Icon": "🌐", "SupportsTextInput": True,  "AutoProcess": False},
        {"ModeName": "resume",         "DisplayName": "Resume Analyzer",    "Icon": "📄", "SupportsTextInput": True,  "AutoProcess": False},
        {"ModeName": "question_paper", "DisplayName": "Question Paper",     "Icon": "📚", "SupportsTextInput": True,  "AutoProcess": False},
        {"ModeName": "legal",          "DisplayName": "Legal Simplifier",   "Icon": "⚖️", "SupportsTextInput": True,  "AutoProcess": False},
        {"ModeName": "medical",        "DisplayName": "Medical Report",     "Icon": "🩺", "SupportsTextInput": False, "AutoProcess": True},
    ]
    for m in default_modes:
        if not db_session.query(Mode).filter(Mode.ModeName == m["ModeName"]).first():
            db_session.add(Mode(**m))
    db_session.commit()
