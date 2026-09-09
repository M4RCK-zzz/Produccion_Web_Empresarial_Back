from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 1. Cargar la base de datos y los modelos explícitamente
from app.database.connection import engine, Base
import app.database.models  # 👈 OBLIGATORIO para registrar modelos en SQLAlchemy

# Routers
from app.api.clientes import router as clientes_router
from app.api.comentarios import router as comentarios_router
from app.api.metricas import router as metricas_router
from app.api.nltk import router as nltk_router
from app.api.scipy import router as scipy_router
from app.api.reportes import router as reportes_router
from app.api.dashboard_api import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas si no existen al iniciar la aplicación
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error al conectar/crear tablas en la BD: {e}")
    yield


# Deshabilitar redirección automática de slashes para evitar romper peticiones CORS
app = FastAPI(
    title="Empresa Inteligente API", 
    lifespan=lifespan,
    redirect_slashes=False
)

# Configuración de CORS para producción y desarrollo local
origins = [
    "https://produccion-web-empresarial-front.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*-.*\.vercel\.app",  # Permite previews de Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra los routers
app.include_router(clientes_router)
app.include_router(comentarios_router)
app.include_router(metricas_router)
app.include_router(nltk_router)
app.include_router(scipy_router)
app.include_router(reportes_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"status": "online", "message": "API ejecutándose correctamente"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Excepción no controlada en {request.url}: {exc}")
    
    origin = request.headers.get("origin", "")
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Error interno del servidor: {str(exc)}"},
    )
    
    # Inyectar CORS siempre que exista un origen en la petición
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
    return response