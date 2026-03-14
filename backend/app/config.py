from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    FRONTEND_VERIFY_URL: str = "http://localhost:4200"
    VECTOR_DB_PATH: str = "data/vector_dbs"
    STATIC_VECTOR_DB_PATH: str = "data/static/vector_dbs"
    UPLOAD_BASE: str = "data/uploads"
    PROFILE_PICS_PATH: str = "data/profile_pics"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
