from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _normalize(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def hash_password(password: str) -> str:
    return pwd_context.hash(_normalize(password))

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(_normalize(password), hashed)
