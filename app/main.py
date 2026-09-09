from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.clientes import router as clientes_router
from app.api.comentarios import router as comentarios_router
from app.api.metricas import router as metricas_router
from app.api.nltk import router as nltk_router
from app.api.scipy import router as scipy_router
from app.api.reportes import router as reportes_router
from app.api.dashboard_api import router as dashboard_router  # NUEVO

app = FastAPI(title="Empresa Inteligente API")

origins = [
    "https://produccion-web-empresarial-front.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes_router,   prefix="/api/clientes",   tags=["Clientes"])
app.include_router(comentarios_router, prefix="/api/comentarios", tags=["Comentarios"])
app.include_router(metricas_router,   prefix="/api/metricas",   tags=["Métricas"])
app.include_router(nltk_router,       prefix="/api/nltk",       tags=["NLTK"])
app.include_router(scipy_router,      prefix="/api/scipy",      tags=["SciPy"])
app.include_router(reportes_router,   prefix="/api/reportes",   tags=["Reportes"])
app.include_router(dashboard_router,  prefix="/api/dashboard",  tags=["Dashboard"])  # NUEVO


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Excepción no controlada en {request.url}: {exc}")
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Error interno del servidor: {str(exc)}"},
    )
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
