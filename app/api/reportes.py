from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

router = APIRouter()

# Schema para el cuerpo del reporte personalizado
class GenerarReportePayload(BaseModel):
    tipo: str
    formato: str

# 1. Endpoint para obtener las métricas generales del reporte
@router.get("/general")
async def obtener_reporte_general():
    try:
        # Datos mock/ejemplo o conectarlos con tu servicio de reportes
        data = {
            "total_comentarios": 120,
            "positivos": 75,
            "neutros": 30,
            "negativos": 15,
            "promedio_polaridad": 0.65
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener reporte general: {str(e)}"
        )

# 2. Endpoint para descargar reporte directo en PDF
@router.get("/exportar/pdf")
async def descargar_reporte_pdf():
    try:
        contenido_pdf = b"%PDF-1.4 ... (Contenido binario del PDF)"
        return Response(
            content=contenido_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=reporte_general.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar PDF: {str(e)}"
        )

# 3. Endpoint POST para generar reportes dinámicos por tipo/formato
@router.post("/generar")
async def generar_reporte(payload: GenerarReportePayload):
    try:
        if payload.formato.upper() == "PDF":
            contenido = b"%PDF-1.4 ... (Contenido del Reporte PDF)"
            media_type = "application/pdf"
        elif payload.formato.upper() == "CSV":
            contenido = b"id,nombre,tipo\n1,Reporte NLP,NLP"
            media_type = "text/csv"
        else:
            contenido = b"id,nombre\n1,Reporte Excel"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        return Response(
            content=contenido,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=reporte.{payload.formato.lower()}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar reporte: {str(e)}"
        )