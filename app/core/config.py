# backend/app/core/config.py
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Empresa Inteligente API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/empresa_inteligente")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Orígenes CORS permitidos
    CORS_ORIGINS: List[str] = [
        "https://produccion-web-empresarial-front.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ]

settings = Settings()