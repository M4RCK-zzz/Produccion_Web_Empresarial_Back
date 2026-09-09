from fastapi import APIRouter, Body, HTTPException, status
from app.services.nltk_service import analizar_texto_nltk

# Prefijo y tags centralizados correctamente
router = APIRouter(prefix="/api/nltk", tags=["NLTK"])


@router.post("/analizar")
def analizar_comentario(payload: dict = Body(...)):
    texto = payload.get("texto", "") if payload else ""
    if not isinstance(texto, str):
        texto = str(texto)

    resultado = analizar_texto_nltk(texto)

    return {
        "sentimiento": resultado.get("sentimiento", "neutral"),
        "polaridad": resultado.get("polaridad", 0.0),
        "score": resultado.get("score", {}),
        "confianza": resultado.get("confianza", 0.0),
        "categoria_detectada": resultado.get("categoria_detectada", "GENERAL"),
        "tokens": resultado.get("tokens", []),
        "palabras_frecuentes": resultado.get("palabras_frecuentes", []),
        "sentimiento_predominante": resultado.get("sentimiento", "neutral"),
        "polaridad_score": resultado.get("polaridad", 0.0),
        "entidades": [],
        "motor": "NLTK / SciPy Wrapper",
        "estado": "Conectado",
    }


@router.post("/palabras-frecuentes")
def obtener_palabras_frecuentes(payload: dict = Body(...)):
    texto = payload.get("texto", "") if payload else ""
    if not isinstance(texto, str):
        texto = str(texto)

    resultado = analizar_texto_nltk(texto)
    return {"palabras_frecuentes": resultado.get("palabras_frecuentes", [])}


@router.post("/clasificar")
def clasificar_texto(payload: dict = Body(...)):
    texto = payload.get("texto", "") if payload else ""
    if not isinstance(texto, str):
        texto = str(texto)

    resultado = analizar_texto_nltk(texto)
    return {
        "categoria_detectada": resultado.get("categoria_detectada", "GENERAL"),
        "confianza": resultado.get("confianza", 0.0),
    }