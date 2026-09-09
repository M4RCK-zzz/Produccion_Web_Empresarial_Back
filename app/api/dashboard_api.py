from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import AnalisisNlpModel, ComentarioModel, TiempoAtencionModel

# Define el prefijo completo de la API en el APIRouter
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


@router.get("/graficos")
@router.get("/graficos/")
def obtener_graficos_dashboard(db: Session = Depends(get_db)):
    """
    Devuelve los datos reales para los dos gráficos del Dashboard:
    - tiempos_semana: tiempos de atención agrupados por día (últimos 7 días)
    - distribucion_categorias: conteo de comentarios por categoría NLTK
    """
    hoy = date.today()

    # --- Gráfico 1: Tiempos de atención por día (últimos 7 días) ---
    tiempos_semana = []
    for offset in range(6, -1, -1):
        dia = hoy - timedelta(days=offset)
        promedio = (
            db.query(func.avg(TiempoAtencionModel.tiempo_minutos))
            .filter(TiempoAtencionModel.fecha == dia)
            .scalar()
        )
        tiempos_semana.append({
            "dia": DIAS_ES[dia.weekday()],
            "tiempo": round(float(promedio), 2) if promedio else 0,
        })

    # --- Gráfico 2: Distribución de categorías desde comentarios analizados ---
    categorias_raw = (
        db.query(ComentarioModel.categoria, func.count(ComentarioModel.id))
        .filter(ComentarioModel.categoria.isnot(None))
        .group_by(ComentarioModel.categoria)
        .all()
    )

    distribucion = [
        {"name": cat or "Sin categoría", "value": count}
        for cat, count in categorias_raw
    ]

    # Si no hay datos reales de categorías, usar las del análisis NLP
    if not distribucion:
        nlp_cats = (
            db.query(AnalisisNlpModel.categoria_detectada, func.count(AnalisisNlpModel.id))
            .filter(AnalisisNlpModel.categoria_detectada.isnot(None))
            .group_by(AnalisisNlpModel.categoria_detectada)
            .all()
        )
        distribucion = [
            {"name": cat or "Sin categoría", "value": count}
            for cat, count in nlp_cats
        ]

    return {
        "tiempos_semana": tiempos_semana,
        "distribucion_categorias": distribucion,
    }