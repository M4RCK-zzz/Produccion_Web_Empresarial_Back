from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import ComentarioModel, AnalisisNlpModel, TiempoAtencionModel

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _obtener_graficos(db: Session) -> dict:
    hoy = date.today()
    meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    tendencia_meses = []
    
    for i in range(5, -1, -1):
        ano_target = hoy.year
        mes_target = hoy.month - i
        while mes_target <= 0:
            mes_target += 12
            ano_target -= 1

        primer_dia = date(ano_target, mes_target, 1)
        if mes_target == 12:
            ultimo_dia = date(ano_target + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(ano_target, mes_target + 1, 1) - timedelta(days=1)

        total_comentarios = (
            db.query(ComentarioModel)
            .filter(
                func.date(ComentarioModel.fecha) >= primer_dia,
                func.date(ComentarioModel.fecha) <= ultimo_dia,
            )
            .count()
        )

        positivos = (
            db.query(ComentarioModel)
            .join(AnalisisNlpModel, ComentarioModel.id == AnalisisNlpModel.comentario_id)
            .filter(
                func.date(ComentarioModel.fecha) >= primer_dia,
                func.date(ComentarioModel.fecha) <= ultimo_dia,
                AnalisisNlpModel.confianza > 0.05,
            )
            .count()
        )

        negativos = max(total_comentarios - positivos, 0)

        tendencia_meses.append({
            "mes": meses_nombres[primer_dia.month - 1],
            "comentarios": total_comentarios,
            "positivos": positivos,
            "negativos": negativos,
        })

    # Distribución por sentimiento
    total_analisis = db.query(AnalisisNlpModel).count()
    pos_total = db.query(AnalisisNlpModel).filter(AnalisisNlpModel.confianza > 0.05).count()
    neg_total = db.query(AnalisisNlpModel).filter(AnalisisNlpModel.confianza < -0.05).count()
    neu_total = max(total_analisis - pos_total - neg_total, 0)

    # Tiempo promedio de atención
    tiempo_prom_scalar = db.query(func.avg(TiempoAtencionModel.tiempo_minutos)).scalar()
    tiempo_prom = round(float(tiempo_prom_scalar), 2) if tiempo_prom_scalar is not None else 0.0

    # ✅ Agrupamiento corregido: consultar categoría desde AnalisisNlpModel
    categorias_query = (
        db.query(
            AnalisisNlpModel.categoria_detectada,
            func.count(AnalisisNlpModel.id)
        )
        .group_by(AnalisisNlpModel.categoria_detectada)
        .all()
    )
    
    distribucion_categorias = [
        {"categoria": cat or "GENERAL", "total": cantidad}
        for cat, cantidad in categorias_query
    ] if categorias_query else [{"categoria": "GENERAL", "total": total_analisis}]

    return {
        "tendencia_mensual": tendencia_meses,
        "distribucion_sentimiento": [
            {"nombre": "Positivos", "valor": pos_total},
            {"nombre": "Neutros", "valor": neu_total},
            {"nombre": "Negativos", "valor": neg_total},
        ],
        "distribucion_categorias": distribucion_categorias,
        "tiempo_promedio_minutos": tiempo_prom,
    }


@router.get("/graficos")
def obtener_graficos_dashboard(db: Session = Depends(get_db)):
    """Retorna los datos estructurados para los gráficos del Dashboard."""
    try:
        return _obtener_graficos(db)
    except Exception as e:
        print(f"Error en /api/dashboard/graficos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar los datos de gráficos: {str(e)}"
        )