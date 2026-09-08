from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import ComentarioModel, ClienteModel  # Asegúrate de importar ClienteModel
from app.services.nltk_service import analizar_texto_nltk

router = APIRouter()

# --- Esquemas Pydantic ---
class ComentarioBase(BaseModel):
    contenido: str
    canal: Optional[str] = "web"
    estado: Optional[str] = "pendiente"
    categoria: Optional[str] = None
    cliente_id: Optional[int] = None

class ComentarioCreate(ComentarioBase):
    pass

# Esquema extendido para incluir datos de la tabla Clientes y de NLP
class ComentarioResponse(ComentarioBase):
    id: int
    procesado: Optional[bool] = False
    fecha: Optional[datetime] = None
    
    # Nuevos campos para que el Frontend los reconozca directamente
    cliente: Optional[str] = "Cliente Anónimo"
    empresa: Optional[str] = "N/A"
    departamento: Optional[str] = "General"
    polaridad: Optional[float] = 0.0
    sentimiento: Optional[str] = "Pendiente"

    class Config:
        from_attributes = True

# --- Endpoints de Rutas Estáticas / Lista ---

@router.get("", response_model=List[ComentarioResponse])
@router.get("/", response_model=List[ComentarioResponse])
def obtener_comentarios(db: Session = Depends(get_db)):
    try:
        # Consulta con LEFT JOIN hacia la tabla clientes
        resultados = db.query(ComentarioModel, ClienteModel)\
            .outerjoin(ClienteModel, ComentarioModel.cliente_id == ClienteModel.id)\
            .all()

        respuesta = []
        for com, cli in resultados:
            respuesta.append({
                "id": com.id,
                "contenido": com.contenido,
                "canal": com.canal,
                "estado": com.estado,
                "categoria": com.categoria,
                "cliente_id": com.cliente_id,
                "procesado": com.procesado,
                "fecha": com.fecha,
                # Datos extraídos del JOIN
                "cliente": cli.nombre if cli else "Cliente Anónimo",
                "empresa": cli.empresa if cli else "Empresa N/A",
                "departamento": com.categoria or "General",
                # Datos de NLP (si existen en el modelo)
                "polaridad": getattr(com, "polaridad", 0.0),
                "sentimiento": getattr(com, "sentimiento", "Pendiente")
            })

        return respuesta
    except Exception as e:
        print(f"Error en GET /api/comentarios: {e}")
        return []

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

# --- Endpoints de Análisis Masivo ---

@router.post("/analisis-masivo")
@router.post("/analisis-masivo/")
def ejecutar_analisis_masivo(db: Session = Depends(get_db)):
    try:
        comentarios = db.query(ComentarioModel).all()
        if not comentarios:
            return {"message": "No hay comentarios para analizar", "procesados": 0}

        procesados_count = 0
        for com in comentarios:
            resultado = analizar_texto_nltk(com.contenido)

            if hasattr(com, "sentimiento"):
                com.sentimiento = resultado.get("sentimiento", "Neutro")
            if hasattr(com, "polaridad"):
                com.polaridad = resultado.get("polaridad", 0.0)
            if hasattr(com, "categoria"):
                com.categoria = resultado.get("categoria_detectada", com.categoria)

            com.procesado = True
            com.estado = "analizado"
            procesados_count += 1

        db.commit()
        return {
            "message": "Análisis masivo completado exitosamente",
            "procesados": procesados_count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el análisis masivo: {str(e)}",
        )

# --- Endpoints Dinámicos (Al final) ---

@router.get("/{id}", response_model=ComentarioResponse)
def obtener_comentario(id: int, db: Session = Depends(get_db)):
    comentario = db.query(ComentarioModel).filter(ComentarioModel.id == id).first()
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )
    return comentario