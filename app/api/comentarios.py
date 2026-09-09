from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import ComentarioModel, ClienteModel, AnalisisNlpModel
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

class ComentarioResponse(ComentarioBase):
    id: int
    procesado: Optional[bool] = False
    fecha: Optional[datetime] = None
    
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
        # LEFT JOIN con clientes y analisis_nlp
        resultados = db.query(ComentarioModel, ClienteModel, AnalisisNlpModel)\
            .outerjoin(ClienteModel, ComentarioModel.cliente_id == ClienteModel.id)\
            .outerjoin(AnalisisNlpModel, ComentarioModel.id == AnalisisNlpModel.comentario_id)\
            .all()

        respuesta = []
        for com, cli, nlp in resultados:
            polaridad_val = nlp.confianza if nlp and nlp.confianza is not None else 0.0
            
            # Lógica para inferir el texto de sentimiento
            if not com.procesado:
                sentimiento_str = "Pendiente"
            elif polaridad_val > 0.05:
                sentimiento_str = "Positivo"
            elif polaridad_val < -0.05:
                sentimiento_str = "Negativo"
            else:
                sentimiento_str = "Neutro"

            respuesta.append({
                "id": com.id,
                "contenido": com.contenido,
                "canal": com.canal,
                "estado": com.estado,
                "categoria": com.categoria,
                "cliente_id": com.cliente_id,
                "procesado": com.procesado,
                "fecha": com.fecha,
                "cliente": cli.nombre if cli else f"Cliente #{com.cliente_id or com.id}",
                "empresa": cli.empresa if cli else "N/A",
                "departamento": com.categoria or "General",
                "polaridad": polaridad_val,
                "sentimiento": sentimiento_str
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

            # 1. Actualizar estado de la tabla comentarios
            com.procesado = True
            com.estado = "analizado"
            if resultado.get("categoria_detectada"):
                com.categoria = resultado.get("categoria_detectada")

            # 2. Insertar o actualizar registro en analisis_nlp
            registro_nlp = db.query(AnalisisNlpModel).filter(AnalisisNlpModel.comentario_id == com.id).first()
            if not registro_nlp:
                registro_nlp = AnalisisNlpModel(comentario_id=com.id)
                db.add(registro_nlp)

            registro_nlp.confianza = resultado.get("polaridad", 0.0)
            registro_nlp.categoria_detectada = resultado.get("categoria_detectada", com.categoria)

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