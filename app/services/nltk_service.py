import nltk
from collections import Counter

# Descarga preventiva de todos los paquetes de datos requeridos por NLTK
recursos_nltk = ['punkt', 'punkt_tab', 'stopwords']

for recurso in recursos_nltk:
    try:
        nltk.data.find(f'tokenizers/{recurso}' if 'punkt' in recurso else f'corpora/{recurso}')
    except LookupError:
        nltk.download(recurso, quiet=True)


def analizar_texto_nltk(texto: str) -> dict:
    if not texto or not texto.strip():
        return {
            "idioma": "es",
            "cantidad_palabras": 0,
            "tokens": [],
            "palabras_frecuentes": [],
            "categoria_detectada": "CONSULTA",
            "confianza": 0.0
        }

    palabras = [p.lower() for p in nltk.word_tokenize(texto) if p.isalnum()]
    
    try:
        stopwords_es = set(nltk.corpus.stopwords.words('spanish'))
    except Exception:
        stopwords_es = set()
    
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