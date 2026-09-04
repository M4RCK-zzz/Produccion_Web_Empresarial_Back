# backend/app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_password(password_plana: str, password_hash: str) -> bool:
    return pwd_context.verify(password_plana, password_hash)

def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)