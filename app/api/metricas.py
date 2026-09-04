from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def obtener_metricas():
    return {
        "eficienciaOperativa": "94.2%",
        "satisfaccionNLTK": "88.4%",
        "procesamientoSciPy": "1.2s",
        "conversionGlobal": "6.8%"
    }