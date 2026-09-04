import numpy as np
from scipy import optimize, interpolate

def calcular_estadisticas_avanzadas(valores: list) -> dict:
    arr = np.array(valores, dtype=float)
    if arr.size == 0:
        return {"error": "La lista de valores está vacía"}
    
    return {
        "cantidad": int(arr.size),
        "media": round(float(np.mean(arr)), 2),
        "mediana": round(float(np.median(arr)), 2),
        "desviacion_estandar": round(float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0, 2),
        "minimo": float(np.min(arr)),
        "maximo": float(np.max(arr)),
        "percentil_25": round(float(np.percentile(arr, 25)), 2),
        "percentil_75": round(float(np.percentile(arr, 75)), 2)
    }

def ejecutar_optimizacion_lineal(parametros: dict) -> dict:
    # Ejemplo de optimización simple con SciPy (minimización de una función de costo cuadrática)
    # Minimizar f(x) = (x[0] - 3)**2 + (x[1] - 5)**2 sujeta a recursos
    def objetivo(x):
        return (x[0] - 3)**2 + (x[1] - 5)**2

    x0 = [0.0, 0.0]
    resultado = optimize.minimize(objetivo, x0, method='Nelder-Mead')
    
    return {
        "recurso_a": round(float(resultado.x[0]), 2),
        "recurso_b": round(float(resultado.x[1]), 2),
        "costo": round(float(resultado.fun) * 100 + 500, 2),
        "exito": bool(resultado.success)
    }

def ejecutar_interpolacion(x_vals: list, y_vals: list, x_nuevo: float) -> dict:
    f_interp = interpolate.interp1d(x_vals, y_vals, kind='linear', fill_value="extrapolate")
    y_nuevo = float(f_interp(x_nuevo))
    return {
        "x_interpola": x_nuevo,
        "y_estimado": round(y_nuevo, 2)
    }