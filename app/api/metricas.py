from datetime import date, timedelta
from fastapi import APIRouter, Depends, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import (
    ComentarioModel,
    ClienteModel,
    AnalisisNlpModel,
    TiempoAtencionModel,
)

# ✅ Solución: Definir el prefijo explícitamente en el router
router = APIRouter(prefix="/api/metricas", tags=["Métricas"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calcular_kpis(db: Session) -> dict:
    """Calcula los KPIs principales desde la base de datos real."""
    total_comentarios = db.query(ComentarioModel).count()
    procesados = db.query(ComentarioModel).filter(ComentarioModel.procesado.is_(True)).count()
    porcentaje_procesado = round((procesados / total_comentarios * 100), 1) if total_comentarios else 0.0

    # Satisfacción: cantidad de análisis con confianza > 0.05
    positivos = (
        db.query(AnalisisNlpModel)
        .filter(AnalisisNlpModel.confianza > 0.05)
        .count()
    )
    satisfaccion = round((positivos / procesados * 100), 1) if procesados else 0.0

    # Tiempo promedio de atención en minutos
    tiempo_prom = db.query(func.avg(TiempoAtencionModel.tiempo_minutos)).scalar()
    tiempo_prom = round(float(tiempo_prom), 2) if tiempo_prom is not None else 0.0

    # Conversión: clientes con al menos un comentario positivo / total clientes
    total_clientes = db.query(ClienteModel).filter(ClienteModel.activo.is_(True)).count()
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
    """Devuelve los últimos 6 meses agrupados por mes para el gráfico."""
    hoy = date.today()
    meses = []
    NOMBRES_MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                   "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    for i in range(5, -1, -1):
        # Cálculo exacto de mes y año evitando desfases por timedelta de 30 días
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
    tiempo_prom = round(float(tiempo_prom), 1) if tiempo_prom is not None else 0.0

    total_com = db.query(ComentarioModel).count()
    procesados = db.query(ComentarioModel).filter(ComentarioModel.procesado.is_(True)).count()
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

# ✅ Soporta GET /api/metricas y /api/metricas/
@router.get("/", status_code=200)
def obtener_metricas(db: Session = Depends(get_db)):
    """Devuelve KPIs, tendencia mensual y desglose de indicadores."""
    kpis = _calcular_kpis(db)
    return {
        "kpis": kpis,
        "tendencia": _tendencia_semanal(db),
        "desglose": _desglose_indicadores(db),
    }


# ✅ Soporta GET /api/metricas/exportar y /api/metricas/exportar/
@router.get("/exportar")
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