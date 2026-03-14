from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.auth import router as auth_router
from app.api.upload import router as upload_router
from app.api.routes import router as chat_router
from app.db.database import engine, SessionLocal, Base
from app.db.models import seed_modes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Production RAG System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000", "http://127.0.0.1:4200", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve profile pics as static files
os.makedirs("data/profile_pics", exist_ok=True)
app.mount("/static/profile_pics", StaticFiles(directory="data/profile_pics"), name="profile_pics")

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(chat_router)

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        seed_modes(db)
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Production RAG System v2.0 running", "docs": "/docs"}
