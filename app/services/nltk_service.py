# backend/app/services/nltk_service.py
import nltk
from collections import Counter

# Asegurarse de tener los recursos básicos descargados
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

def analizar_texto_nltk(texto: str) -> dict:
    palabras = [p.lower() for p in nltk.word_tokenize(texto) if p.isalnum()]
    stopwords_es = set(nltk.corpus.stopwords.words('spanish')) if 'spanish' in nltk.corpus.stopwords.fileids() else set()
    
    palabras_limpias = [p for p in palabras if p not in stopwords_es]
    conteo = Counter(palabras_limpias)
    
    palabras_frecuentes = [{"palabra": palabra, "frecuencia": freq} for palabra, freq in conteo.most_common(5)]
    
    # Lógica heurística de categorización simple
    categoria = "CONSULTA"
    texto_lower = texto.lower()
    if any(k in texto_lower for k in ["excelente", "rápido", "bueno", "gracias"]):
        categoria = "FELICITACION"
    elif any(k in texto_lower for k in ["problema", "fallo", "error", "tardó", "reclamo"]):
        categoria = "RECLAMO"
    elif any(k in texto_lower for k in ["soporte", "ayuda", "incidencia"]):
        categoria = "SOPORTE"

    return {
        "idioma": "es",
        "cantidad_palabras": len(palabras),
        "tokens": palabras_limpias,
        "palabras_frecuentes": palabras_frecuentes,
        "categoria_detectada": categoria,
        "confianza": 0.9250
    }