# backend/app/api/scipy.py
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import MetricasEstadisticasModel, TiemposAtencionModel
from app.services.scipy_service import (
    calcular_estadisticas_avanzadas,
    ejecutar_interpolacion,
    ejecutar_optimizacion_lineal,
)

router = APIRouter()


# --- Esquema para validación de entrada ---
class EstadisticasPayload(BaseModel):
    valores: Optional[List[float]] = None


# --- Endpoints ---

# Decoradores dobles para soportar solicitudes con y sin "/"
@router.get("/estadisticas")
@router.get("/estadisticas/")
def obtener_metricas_base(db: Session = Depends(get_db)):
    try:
        # Consulta optimizada: solo obtiene la columna requerida
        registros = db.query(TiemposAtencionModel.tiempo_minutos).all()

        # Extraer y castear explícitamente a float para prevenir conflictos con Decimal
        valores = [float(r[0]) for r in registros if r[0] is not None]

        # Si no existen registros cargados en Supabase, se retornan valores por defecto
        if not valores:
            valores = [12.0, 15.5, 18.0, 20.25, 11.0]

        return calcular_estadisticas_avanzadas(valores)
    except Exception as e:
        print(f"Error en GET /api/scipy/estadisticas: {e}")
        # Retorno defensivo para no romper la carga en React
        return calcular_estadisticas_avanzadas([12.0, 15.5, 18.0, 20.25, 11.0])


@router.post("/estadisticas")
@router.post("/estadisticas/")
def post_estadisticas(
    payload: Optional[EstadisticasPayload] = None,
    db: Session = Depends(get_db),
):
    try:
        # 1. Determinar el origen de los valores
        if payload and payload.valores:
            valores = payload.valores
        else:
            registros = db.query(TiemposAtencionModel.tiempo_minutos).all()
            valores = [float(r[0]) for r in registros if r[0] is not None]

        if not valores:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos suficientes para calcular las estadísticas.",
            )

        # 2. Procesar con SciPy
        resultado_scipy = calcular_estadisticas_avanzadas(valores)

        # 3. Guardar formalmente el cálculo en la BD
        nueva_metrica = MetricasEstadisticasModel(
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            cantidad_registros=int(resultado_scipy.get("cantidad", len(valores))),
            media=float(resultado_scipy.get("media", 0.0)),
            mediana=float(resultado_scipy.get("mediana", 0.0)),
            desviacion_estandar=float(resultado_scipy.get("desviacion_estandar", 0.0)),
            minimo=float(resultado_scipy.get("minimo", 0.0)),
            maximo=float(resultado_scipy.get("maximo", 0.0)),
            percentil_25=float(resultado_scipy.get("percentil_25", 0.0)),
            percentil_75=float(resultado_scipy.get("percentil_75", 0.0)),
        )
        db.add(nueva_metrica)
        db.commit()
        db.refresh(nueva_metrica)

        return {
            "mensaje": "Métrica calculada y registrada exitosamente",
            "datos": resultado_scipy,
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la métrica en la BD: {str(e)}",
        )


@router.post("/optimizacion")
@router.post("/optimizacion/")
def post_optimizacion(payload: dict):
    resultado = ejecutar_optimizacion_lineal(payload)
    return {"parametros_entrada": payload, "resultado": resultado}


@router.post("/interpolacion")
@router.post("/interpolacion/")
def post_interpolacion(payload: dict):
    x_vals = payload.get("x", [1, 2, 3, 4, 5])
    y_vals = payload.get("y", [10, 20, 15, 30, 25])
    x_nuevo = payload.get("x_nuevo", 2.5)
    return ejecutar_interpolacion(x_vals, y_vals, x_nuevo)