from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from app.database.connection import get_db
from app.database.models import (
    ComentarioModel,
    ClienteModel,
    AnalisisNlpModel,
    TiempoAtencionModel,
    MetricasEstadisticaModel,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calcular_kpis(db: Session) -> dict:
    """Calcula los KPIs principales desde la base de datos real."""
    total_comentarios = db.query(ComentarioModel).count()
    procesados = db.query(ComentarioModel).filter(ComentarioModel.procesado == True).count()
    porcentaje_procesado = round((procesados / total_comentarios * 100), 1) if total_comentarios else 0.0

    # Satisfacción: promedio de confianza de análisis positivos
    positivos = (
        db.query(AnalisisNlpModel)
        .filter(AnalisisNlpModel.confianza > 0.05)
        .count()
    )
    satisfaccion = round((positivos / procesados * 100), 1) if procesados else 0.0

    # Tiempo promedio de atención en minutos
    tiempo_prom = db.query(func.avg(TiempoAtencionModel.tiempo_minutos)).scalar()
    tiempo_prom = round(float(tiempo_prom), 2) if tiempo_prom else 0.0

    # Conversión: clientes con al menos un comentario positivo / total clientes
    total_clientes = db.query(ClienteModel).filter(ClienteModel.activo == True).count()
    clientes_con_positivo = (
        db.query(ComentarioModel.cliente_id)
        .join(AnalisisNlpModel, ComentarioModel.id == AnalisisNlpModel.comentario_id)
        .filter(AnalisisNlpModel.confianza > 0.05)
        .distinct()
        .count()
    )
    conversion = round((clientes_con_positivo / total_clientes * 100), 1) if total_clientes else 0.0

    return {
        "eficiencia_operativa": porcentaje_procesado,
        "satisfaccion_nltk": satisfaccion,
        "procesamiento_scipy": tiempo_prom,
        "conversion_global": conversion,
    }


def _tendencia_semanal(db: Session) -> list:
    """Devuelve los últimos 6 meses agrupados por mes para el gráfico de Recharts."""
    hoy = date.today()
    meses = []
    NOMBRES_MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                   "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    for i in range(5, -1, -1):
        # Primer día del mes i meses atrás
        primer_dia = (hoy.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        if primer_dia.month == 12:
            ultimo_dia = primer_dia.replace(year=primer_dia.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            ultimo_dia = primer_dia.replace(month=primer_dia.month + 1, day=1) - timedelta(days=1)

        total = (
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

        meses.append({
            "mes": NOMBRES_MES[primer_dia.month - 1],
            "comentarios": total,
            "positivos": positivos,
            "negativos": total - positivos,
        })

    return meses


def _desglose_indicadores(db: Session) -> list:
    """Genera el desglose de la tabla inferior de Métricas."""
    tiempo_prom = db.query(func.avg(TiempoAtencionModel.tiempo_minutos)).scalar()
    tiempo_prom = round(float(tiempo_prom), 1) if tiempo_prom else 0.0

    total_com = db.query(ComentarioModel).count()
    procesados = db.query(ComentarioModel).filter(ComentarioModel.procesado == True).count()
    tasa_proc = round(procesados / total_com * 100, 1) if total_com else 0.0

    return [
        {
            "indicador": "Tiempo de Respuesta Promedio",
            "categoria": "Soporte",
            "valor": f"{tiempo_prom} min",
            "estado": "Óptimo" if tiempo_prom < 30 else "En revisión",
        },
        {
            "indicador": "Tasa de Procesamiento NLP",
            "categoria": "Análisis",
            "valor": f"{tasa_proc}%",
            "estado": "Óptimo" if tasa_proc >= 80 else "En revisión",
        },
        {
            "indicador": "Comentarios Totales",
            "categoria": "Atención",
            "valor": str(total_com),
            "estado": "Óptimo",
        },
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
@router.get("/")
def obtener_metricas(db: Session = Depends(get_db)):
    """Devuelve KPIs, tendencia mensual y desglose de indicadores."""
    kpis = _calcular_kpis(db)
    return {
        "kpis": kpis,
        "tendencia": _tendencia_semanal(db),
        "desglose": _desglose_indicadores(db),
    }


@router.get("/exportar")
@router.get("/exportar/")
def exportar_metricas(db: Session = Depends(get_db)):
    """Exporta las métricas como CSV descargable."""
    kpis = _calcular_kpis(db)
    tendencia = _tendencia_semanal(db)

    lineas = [
        "Reporte de Métricas - Empresa Inteligente",
        "",
        "KPIs PRINCIPALES",
        f"Eficiencia Operativa,{kpis['eficiencia_operativa']}%",
        f"Satisfacción NLTK,{kpis['satisfaccion_nltk']}%",
        f"Procesamiento SciPy (tiempo prom),{kpis['procesamiento_scipy']} min",
        f"Conversión Global,{kpis['conversion_global']}%",
        "",
        "TENDENCIA MENSUAL (últimos 6 meses)",
        "Mes,Comentarios,Positivos,Negativos",
    ]
    for fila in tendencia:
        lineas.append(f"{fila['mes']},{fila['comentarios']},{fila['positivos']},{fila['negativos']}")

    csv_content = "\n".join(lineas)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metricas.csv"},
    )
