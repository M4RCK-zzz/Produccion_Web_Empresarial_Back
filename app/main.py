# backend/app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 1. Importar todos los routers
from app.api.clientes import router as clientes_router
from app.api.comentarios import router as comentarios_router
from app.api.scipy import router as scipy_router

app = FastAPI(title="Empresa Inteligente API")

origins = [
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

# 2. Registrar los routers con sus prefijos /api
app.include_router(clientes_router, prefix="/api/clientes", tags=["Clientes"])
app.include_router(comentarios_router, prefix="/api/comentarios", tags=["Comentarios"])
app.include_router(scipy_router, prefix="/api/scipy", tags=["SciPy"])


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