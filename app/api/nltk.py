from fastapi import APIRouter, Body
from app.services.nltk_service import analizar_texto_nltk

router = APIRouter()


@router.post("/analizar")
@router.post("/analizar/")
def analizar_comentario(payload: dict = Body(...)):
    """
    Analiza un texto y devuelve sentimiento, polaridad, tokens y categoría.
    Body: { "texto": "..." }
    """
    texto = payload.get("texto", "")
    resultado = analizar_texto_nltk(texto)

    # Respuesta completa que el frontend necesita para el Laboratorio NLP
    return {
        "sentimiento": resultado["sentimiento"],
        "polaridad": resultado["polaridad"],
        "score": resultado["score"],
        "confianza": resultado["confianza"],
        "categoria_detectada": resultado["categoria_detectada"],
        "tokens": resultado["tokens"],
        "palabras_frecuentes": resultado["palabras_frecuentes"],
        # Campos de compatibilidad con el frontend (AnalisisNLP.tsx)
        "sentimiento_predominante": resultado["sentimiento"],
        "polaridad_score": resultado["polaridad"],
        "entidades": [],          # NER no implementado aún — array vacío
        "motor": "NLTK / SciPy Wrapper",
        "estado": "Conectado",
    }


@router.post("/palabras-frecuentes")
@router.post("/palabras-frecuentes/")
def obtener_palabras_frecuentes(payload: dict = Body(...)):
    """
    Devuelve las 5 palabras más frecuentes del texto.
    Body: { "texto": "..." }
    """
    texto = payload.get("texto", "")
    resultado = analizar_texto_nltk(texto)
    return {"palabras_frecuentes": resultado["palabras_frecuentes"]}


@router.post("/clasificar")
@router.post("/clasificar/")
def clasificar_texto(payload: dict = Body(...)):
    """
    Clasifica el texto en una categoría temática (RECLAMO, CONSULTA, etc.).
    Body: { "texto": "..." }
    """
    texto = payload.get("texto", "")
    resultado = analizar_texto_nltk(texto)
    return {
        "categoria_detectada": resultado["categoria_detectada"],
        "confianza": resultado["confianza"],
    }
