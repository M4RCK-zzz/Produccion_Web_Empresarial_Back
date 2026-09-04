# backend/app/api/comentarios.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import ComentarioModel

router = APIRouter()


# --- Esquemas de Pydantic ---
class ComentarioBase(BaseModel):
    contenido: str
    canal: Optional[str] = "web"
    estado: Optional[str] = "pendiente"
    categoria: Optional[str] = None
    cliente_id: Optional[int] = None


class ComentarioCreate(ComentarioBase):
    pass


class ComentarioResponse(ComentarioBase):
    id: int
    procesado: Optional[bool] = False
    fecha: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Endpoints ---

# Soporta /api/comentarios y /api/comentarios/
@router.get("", response_model=List[ComentarioResponse])
@router.get("/", response_model=List[ComentarioResponse])
def obtener_comentarios(db: Session = Depends(get_db)):
    try:
        comentarios = db.query(ComentarioModel).all()
        return comentarios if comentarios else []
    except Exception as e:
        print(f"Error en GET /api/comentarios: {e}")
        return []


@router.get("/{id}", response_model=ComentarioResponse)
def obtener_comentario(id: int, db: Session = Depends(get_db)):
    comentario = db.query(ComentarioModel).filter(ComentarioModel.id == id).first()
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )
    return comentario


@router.post("", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
def crear_comentario(comentario_in: ComentarioCreate, db: Session = Depends(get_db)):
    try:
        nuevo_comentario = ComentarioModel(**comentario_in.model_dump())
        db.add(nuevo_comentario)
        db.commit()
        db.refresh(nuevo_comentario)
        return nuevo_comentario
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar comentario: {str(e)}",
        )