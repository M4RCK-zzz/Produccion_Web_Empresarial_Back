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
    cliente_nombre: Optional[str] = None
    empresa: Optional[str] = None

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

# --- Helper para construir respuesta enriquecida ---
def _construir_respuesta(com: ComentarioModel, cli: ClienteModel, nlp: AnalisisNlpModel) -> dict:
    """Construye el dict de respuesta con datos de cliente y NLP."""
    polaridad_val = nlp.confianza if (nlp and nlp.confianza is not None) else 0.0

    # Lógica de asignación de sentimiento basada en polaridad y estado
    if not com.procesado:
        sentimiento_str = "Pendiente"
    elif polaridad_val > 0.05:
        sentimiento_str = "Positivo"
    elif polaridad_val < -0.05:
        sentimiento_str = "Negativo"
    else:
        sentimiento_str = "Neutro"

    return {
        "id": com.id,
        "contenido": com.contenido,
        "canal": com.canal,
        "estado": com.estado,
        "categoria": com.categoria,
        "cliente_id": com.cliente_id,
        "procesado": com.procesado,
        "fecha": com.fecha,
        "cliente": cli.nombre if cli else f"Cliente #{com.cliente_id or com.id}",
        "empresa": cli.empresa if (cli and cli.empresa) else "N/A",
        "departamento": com.categoria or "General",
        "polaridad": polaridad_val,
        "sentimiento": sentimiento_str,
    }


# --- Endpoints de Rutas Estáticas / Lista ---

@router.get("", response_model=List[ComentarioResponse])
@router.get("/", response_model=List[ComentarioResponse])
def obtener_comentarios(db: Session = Depends(get_db)):
    try:
        resultados = (
            db.query(ComentarioModel, ClienteModel, AnalisisNlpModel)
            .outerjoin(ClienteModel, ComentarioModel.cliente_id == ClienteModel.id)
            .outerjoin(AnalisisNlpModel, ComentarioModel.id == AnalisisNlpModel.comentario_id)
            .all()
        )

        return [_construir_respuesta(com, cli, nlp) for com, cli, nlp in resultados]
    except Exception as e:
        print(f"Error en GET /api/comentarios: {e}")
        return []


@router.post("", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
def crear_comentario(comentario_in: ComentarioCreate, db: Session = Depends(get_db)):
    try:
        cliente_id_asignado = comentario_in.cliente_id
        cliente_obj = None

        # 1. Busca o crea el cliente si se envió un nombre desde el formulario
        if comentario_in.cliente_nombre and not cliente_id_asignado:
            cliente_existente = db.query(ClienteModel).filter(
                ClienteModel.nombre == comentario_in.cliente_nombre
            ).first()

            if cliente_existente:
                cliente_id_asignado = cliente_existente.id
                cliente_obj = cliente_existente
            else:
                nuevo_cliente = ClienteModel(
                    nombre=comentario_in.cliente_nombre,
                    empresa=comentario_in.empresa or "N/A",
                )
                db.add(nuevo_cliente)
                db.commit()
                db.refresh(nuevo_cliente)
                cliente_id_asignado = nuevo_cliente.id
                cliente_obj = nuevo_cliente
        elif cliente_id_asignado:
            cliente_obj = db.query(ClienteModel).filter(ClienteModel.id == cliente_id_asignado).first()

        # 2. Analiza el texto inmediatamente al crearse
        res_nlp = analizar_texto_nltk(comentario_in.contenido)

        # 3. Guarda el comentario indicando que ya está procesado
        datos_comentario = comentario_in.model_dump(exclude={"cliente_nombre", "empresa"})
        datos_comentario["cliente_id"] = cliente_id_asignado
        datos_comentario["procesado"] = True
        datos_comentario["estado"] = "analizado"
        datos_comentario["categoria"] = res_nlp.get("categoria_detectada")

        nuevo_comentario = ComentarioModel(**datos_comentario)
        db.add(nuevo_comentario)
        db.commit()
        db.refresh(nuevo_comentario)

        # 4. Asocia la entrada en la tabla AnalisisNlpModel
        registro_nlp = AnalisisNlpModel(
            comentario_id=nuevo_comentario.id,
            confianza=res_nlp.get("polaridad", 0.0),
            categoria_detectada=res_nlp.get("categoria_detectada")
        )
        db.add(registro_nlp)
        db.commit()
        db.refresh(registro_nlp)

        return _construir_respuesta(nuevo_comentario, cliente_obj, registro_nlp)

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
            registro_nlp = (
                db.query(AnalisisNlpModel)
                .filter(AnalisisNlpModel.comentario_id == com.id)
                .first()
            )
            if not registro_nlp:
                registro_nlp = AnalisisNlpModel(comentario_id=com.id)
                db.add(registro_nlp)

            registro_nlp.confianza = resultado.get("polaridad", 0.0)
            registro_nlp.categoria_detectada = resultado.get(
                "categoria_detectada", com.categoria
            )

            procesados_count += 1

        db.commit()
        return {
            "message": "Análisis masivo completado exitosamente",
            "procesados": procesados_count,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el análisis masivo: {str(e)}",
        )


# --- Endpoints Dinámicos ---

@router.get("/{id}", response_model=ComentarioResponse)
def obtener_comentario(id: int, db: Session = Depends(get_db)):
    resultado = (
        db.query(ComentarioModel, ClienteModel, AnalisisNlpModel)
        .outerjoin(ClienteModel, ComentarioModel.cliente_id == ClienteModel.id)
        .outerjoin(AnalisisNlpModel, ComentarioModel.id == AnalisisNlpModel.comentario_id)
        .filter(ComentarioModel.id == id)
        .first()
    )
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado",
        )
    com, cli, nlp = resultado
    return _construir_respuesta(com, cli, nlp)