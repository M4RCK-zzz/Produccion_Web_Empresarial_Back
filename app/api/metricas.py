from fastapi import APIRouter

router = APIRouter()

# Doble decorador para evitar problemas de slashes
@router.get("", summary="Obtener métricas del sistema")
@router.get("/", summary="Obtener métricas del sistema")
def obtener_metricas():
    return {
        "eficienciaOperativa": "94.2%",
        "satisfaccionNLTK": "88.4%",
        "procesamientoSciPy": "1.2s",
        "conversionGlobal": "6.8%"
    }