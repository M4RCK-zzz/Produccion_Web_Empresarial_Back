# backend/app/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear el motor de SQLAlchemy apuntando a Supabase
engine = create_engine(settings.DATABASE_URL)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos ORM
Base = declarative_base()

# Dependencia para inyectar la sesión en los endpoints de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()