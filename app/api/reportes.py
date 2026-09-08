from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.reportes_service import generar_archivo_reporte

router = APIRouter()

class ReporteRequest(BaseModel):
    tipo: str
    formato: str

@router.post("/generar")
@router.post("/generar/")
def generar_reporte(payload: ReporteRequest):
    try:
        buffer, media_type, filename = generar_archivo_reporte(payload.tipo, payload.formato)
        
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")