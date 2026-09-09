import os
import joblib
import numpy as np
import nltk
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# 1. Configurar directorio de datos NLTK en /tmp para entornos como Render
nltk_data_dir = os.path.join("/tmp", "nltk_data")
if nltk_data_dir not in nltk.data.path:
    nltk.data.path.append(nltk_data_dir)

# Descarga segura de paquetes NLTK
recursos_nltk = [
    ('punkt', 'tokenizers/punkt'),
    ('punkt_tab', 'tokenizers/punkt_tab'),
    ('stopwords', 'corpora/stopwords')
]

for recurso, ruta in recursos_nltk:
    try:
        nltk.data.find(ruta)
    except LookupError:
        try:
            nltk.download(recurso, download_dir=nltk_data_dir, quiet=True)
        except Exception as e:
            print(f"Error descargando recurso {recurso}: {e}")

# Dataset de entrenamiento inicial en español
DATASET_ENTRENAMIENTO = [
    # Positivos
    ("Excelente servicio y muy rápida atención", "Positivo"),
    ("El soporte técnico resolvió mi problema rápidamente", "Positivo"),
    ("Muy satisfecho con la atención brindada por el equipo", "Positivo"),
    ("La plataforma funciona de manera impecable y eficiente", "Positivo"),
    ("Buen trabajo, todo perfecto y muy rápido", "Positivo"),
    ("Me ayudaron a resolver la duda de inmediato, gracias", "Positivo"),
    ("Gran experiencia, respuesta súper rápida y clara", "Positivo"),
    # Negativos
    ("El soporte técnico tardó más de lo esperado en resolver nuestra incidencia de facturación", "Negativo"),
    ("Pésima atención, no me dieron ninguna solución", "Negativo"),
    ("El servicio es muy lento y presenta constantes fallas", "Negativo"),
    ("Tengo un reclamo grave con respecto a la facturación cobrada", "Negativo"),
    ("Hubo un error en el sistema y no responden mis correos", "Negativo"),
    ("Tardaron días en dar respuesta a mi solicitud de soporte", "Negativo"),
    ("El sistema falló durante la transacción y no recibí ayuda", "Negativo"),
    # Neutros
    ("Quisiera solicitar información sobre los planes disponibles", "Neutro"),
    ("¿Cuál es el horario de atención al cliente?", "Neutro"),
    ("Necesito consultar el estado de mi trámite actual", "Neutro"),
    ("Envié los documentos requeridos a su correo", "Neutro"),
]

def entrenar_modelo():
    """Entrena un Pipeline de ML ligero directamente en memoria."""
    textos = [item[0] for item in DATASET_ENTRENAMIENTO]
    etiquetas = [item[1] for item in DATASET_ENTRENAMIENTO]

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
        ('clf', MultinomialNB())
    ])

    pipeline.fit(textos, etiquetas)
    return pipeline

# Instancia global del modelo ML en memoria
modelo_ml = entrenar_modelo()

def analizar_texto_nltk(texto: str) -> dict:
    if not texto or not texto.strip():
        return {
            "sentimiento": "Neutro",
            "polaridad": 0.0,
            "score": 0.0,
            "tokens": [],
            "palabras_frecuentes": [],
            "categoria_detectada": "CONSULTA",
            "confianza": 0.0
        }

    # 1. Extracción de tokens con fallback seguro si falla la tokenización NLTK
    texto_lower = texto.lower()
    try:
        tokens_raw = nltk.word_tokenize(texto_lower)
    except Exception:
        tokens_raw = texto_lower.split()

    palabras = [p for p in tokens_raw if p.isalnum()]

    try:
        stopwords_es = set(nltk.corpus.stopwords.words('spanish'))
    except Exception:
        stopwords_es = set()

    palabras_limpias = [p for p in palabras if p not in stopwords_es]
    conteo = Counter(palabras_limpias)
    palabras_frecuentes = [{"palabra": p, "frecuencia": f} for p, f in conteo.most_common(5)]

    # 2. Predicción con el Modelo de Machine Learning
    prediccion = modelo_ml.predict([texto])[0]
    probabilidades = modelo_ml.predict_proba([texto])[0]
    clases = list(modelo_ml.classes_)

    idx_pred = clases.index(prediccion)
    confianza = float(probabilidades[idx_pred])

    # Cálculo de la polaridad escalar (-1.0 a 1.0)
    if prediccion == "Positivo":
        polaridad = round(confianza, 2)
    elif prediccion == "Negativo":
        polaridad = round(-confianza, 2)
    else:
        polaridad = 0.0

    # Categorización temática
    if any(k in texto_lower for k in ["excelente", "rápido", "bueno", "gracias"]):
        categoria = "FELICITACION"
    elif any(k in texto_lower for k in ["problema", "fallo", "error", "tardó", "reclamo", "incidencia"]):
        categoria = "RECLAMO"
    elif any(k in texto_lower for k in ["soporte", "ayuda"]):
        categoria = "SOPORTE"
    else:
        categoria = "CONSULTA"

    return {
        "sentimiento": prediccion,
        "polaridad": polaridad,
        "score": polaridad,
        "tokens": palabras_limpias,
        "palabras_frecuentes": palabras_frecuentes,
        "categoria_detectada": categoria,
        "confianza": round(confianza, 4)
    }