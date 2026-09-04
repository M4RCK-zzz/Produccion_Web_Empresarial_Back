# backend/app/api/nltk.py
from fastapi import APIRouter, Body
from app.services.nltk_service import analizar_texto_nltk

router = APIRouter()

@router.post("/analizar")
def analizar_comentario(payload: dict = Body(...)):
    texto = payload.get("texto", "")
    return analizar_texto_nltk(texto)

@router.post("/palabras-frecuentes")
def obtener_palabras_frecuentes(payload: dict = Body(...)):
    texto = payload.get("texto", "")
    resultado = analizar_texto_nltk(texto)
    return {"palabras_frecuentes": resultado["palabras_frecuentes"]}

@router.post("/clasificar")
def clasificar_texto(payload: dict = Body(...)):
    texto = payload.get("texto", "")
    resultado = analizar_texto_nltk(texto)
    return {
        "categoria_detectada": resultado["categoria_detectada"],
        "confianza": resultado["confianza"]
    }