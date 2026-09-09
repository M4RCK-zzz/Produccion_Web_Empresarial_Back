from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    ComentarioModel,
    ClienteModel,
    AnalisisNlpModel,
    TiempoAtencionModel,
    MetricasEstadisticasModel,
    OptimizacionModel,
)
from app.services.scipy_service import (
    calcular_estadisticas_avanzadas,
    ejecutar_interpolacion,
    ejecutar_optimizacion_lineal,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class EstadisticasPayload(BaseModel):
    valores: Optional[List[float]] = None


class OptimizacionEstadoPayload(BaseModel):
    estado: str  # "pendiente" | "en_proceso" | "completado"


class InterpolacionPayload(BaseModel):
    x: List[float] = Field(default_factory=lambda: [1.0, 2.0, 3.0, 4.0, 5.0])
    y: List[float] = Field(default_factory=lambda: [10.0, 20.0, 15.0, 30.0, 25.0])
    x_nuevo: float = 2.5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valores_tiempos(db: Session) -> List[float]:
    registros = db.query(TiempoAtencionModel.tiempo_minutos).all()
    valores = [float(r[0]) for r in registros if r[0] is not None]
    return valores or [12.0, 15.5, 18.0, 20.25, 11.0]


# ---------------------------------------------------------------------------
# Endpoints de estadísticas SciPy
# ---------------------------------------------------------------------------

@router.get("/estadisticas")
@router.get("/estadisticas/")
def obtener_estadisticas(db: Session = Depends(get_db)):
    return calcular_estadisticas_avanzadas(_valores_tiempos(db))


@router.post("/estadisticas")
@router.post("/estadisticas/")
def guardar_estadisticas(
    payload: Optional[EstadisticasPayload] = None,
    db: Session = Depends(get_db),
):
    valores = (payload.valores if payload and payload.valores else None) or _valores_tiempos(db)

    if not valores:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay datos suficientes para calcular las estadísticas.",
        )

    resultado = calcular_estadisticas_avanzadas(valores)

    nueva = MetricasEstadisticasModel(
        fecha_inicio=date.today(),
        fecha_fin=date.today(),
        cantidad_registros=int(resultado.get("cantidad", len(valores))),
        media=float(resultado.get("media", 0.0)),
        mediana=float(resultado.get("mediana", 0.0)),
        desviacion_estandar=float(resultado.get("desviacion_estandar", 0.0)),
        minimo=float(resultado.get("minimo", 0.0)),
        maximo=float(resultado.get("maximo", 0.0)),
        percentil_25=float(resultado.get("percentil_25", 0.0)),
        percentil_75=float(resultado.get("percentil_75", 0.0)),
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return {"mensaje": "Métrica calculada y registrada exitosamente", "datos": resultado}


# ---------------------------------------------------------------------------
# Endpoint de escaneo de sistema
# ---------------------------------------------------------------------------

@router.post("/escaneo")
@router.post("/escaneo/")
def ejecutar_escaneo(db: Session = Depends(get_db)):
    sugerencias = []

    # 1. Verificar comentarios sin procesar
    total = db.query(ComentarioModel).count()
    sin_procesar = db.query(ComentarioModel).filter(ComentarioModel.procesado.is_(False)).count()
    porcentaje_sin_procesar = (sin_procesar / total * 100) if total else 0

    if porcentaje_sin_procesar > 20:
        sugerencias.append({
            "titulo": "Análisis NLP pendiente",
            "categoria": "NLP",
            "impacto": "Alto",
            "descripcion": f"{sin_procesar} comentarios ({porcentaje_sin_procesar:.0f}%) aún no han sido analizados.",
            "beneficio": "Mejora la calidad del análisis de sentimiento",
        })

    # 2. Verificar tiempos de atención
    estadisticas = calcular_estadisticas_avanzadas(_valores_tiempos(db))
    media = estadisticas.get("media", 0)
    if media > 20:
        sugerencias.append({
            "titulo": "Tiempo de atención elevado",
            "categoria": "Atención",
            "impacto": "Alto",
            "descripcion": f"El tiempo promedio de atención es {media:.1f} min, por encima del umbral recomendado (20 min).",
            "beneficio": "Reducción del tiempo de respuesta al cliente",
        })

    # 3. Verificar precisión NLP (confianza promedio)
    confianza_prom = db.query(func.avg(AnalisisNlpModel.confianza)).scalar()
    if confianza_prom and float(confianza_prom) < 0.70:
        sugerencias.append({
            "titulo": "Reentrenamiento de modelo NLP recomendado",
            "categoria": "NLP",
            "impacto": "Medio",
            "descripcion": f"La confianza promedio del modelo es {float(confianza_prom):.0%}. Ampliar el dataset mejorará la precisión.",
            "beneficio": "Mayor precisión en clasificación de sentimientos",
        })

    # 4. Verificar total de clientes activos
    total_clientes = db.query(ClienteModel).filter(ClienteModel.activo.is_(True)).count()
    if total_clientes == 0:
        sugerencias.append({
            "titulo": "Sin clientes activos",
            "categoria": "Clientes",
            "impacto": "Medio",
            "descripcion": "No se registran clientes activos actualmente en la base de datos.",
            "beneficio": "Permite registrar y vincular la actividad de usuarios",
        })

    if not sugerencias:
        sugerencias.append({
            "titulo": "Sistema en estado óptimo",
            "categoria": "Rendimiento",
            "impacto": "Bajo",
            "descripcion": "No se detectaron problemas críticos en el análisis del sistema.",
            "beneficio": "Sin acciones requeridas",
        })

    return {"sugerencias": sugerencias, "total": len(sugerencias)}


# ---------------------------------------------------------------------------
# Endpoints de optimizaciones
# ---------------------------------------------------------------------------

@router.get("/optimizaciones")
@router.get("/optimizaciones/")
def listar_optimizaciones(db: Session = Depends(get_db)):
    items = db.query(OptimizacionModel).order_by(OptimizacionModel.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "nombre": o.nombre,
            "descripcion": o.descripcion,
            "estado": o.estado,
            "costo_inicial": float(o.costo_inicial) if o.costo_inicial is not None else None,
            "costo_optimizado": float(o.costo_optimizado) if o.costo_optimizado is not None else None,
            "resultado": o.resultado,
        }
        for o in items
    ]


@router.patch("/optimizaciones/{id}/estado")
@router.patch("/optimizaciones/{id}/estado/")
def actualizar_estado_optimizacion(
    id: int,
    payload: OptimizacionEstadoPayload,
    db: Session = Depends(get_db),
):
    item = db.query(OptimizacionModel).filter(OptimizacionModel.id == id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimización no encontrada")
    item.estado = payload.estado
    db.commit()
    db.refresh(item)
    return {"id": item.id, "estado": item.estado}


# ---------------------------------------------------------------------------
# Endpoints auxiliares SciPy
# ---------------------------------------------------------------------------

@router.post("/optimizacion")
@router.post("/optimizacion/")
def post_optimizacion(payload: Dict[str, Any]):
    return {"parametros_entrada": payload, "resultado": ejecutar_optimizacion_lineal(payload)}


@router.post("/interpolacion")
@router.post("/interpolacion/")
def post_interpolacion(payload: Optional[InterpolacionPayload] = None):
    data = payload or InterpolacionPayload()
    return ejecutar_interpolacion(
        data.x,
        data.y,
        data.x_nuevo,
    )