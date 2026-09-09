from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.database.models import ComentarioModel, AnalisisNlpModel, ClienteModel

# ✅ Solución: Prefijo explícito y asignación de tags
router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


class GenerarReportePayload(BaseModel):
    tipo: str
    formato: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _datos_reporte(db: Session) -> dict:
    """Genera los datos reales del reporte desde la base de datos."""
    total = db.query(ComentarioModel).count()
    procesados = db.query(ComentarioModel).filter(ComentarioModel.procesado.is_(True)).count()

    positivos = (
        db.query(ComentarioModel)
        .join(AnalisisNlpModel, ComentarioModel.id == AnalisisNlpModel.comentario_id)
        .filter(AnalisisNlpModel.confianza > 0.05)
        .count()
    )
    negativos = (
        db.query(ComentarioModel)
        .join(AnalisisNlpModel, ComentarioModel.id == AnalisisNlpModel.comentario_id)
        .filter(AnalisisNlpModel.confianza < -0.05)
        .count()
    )
    neutros = procesados - positivos - negativos if procesados else 0

    promedio = db.query(func.avg(AnalisisNlpModel.confianza)).scalar()
    total_clientes = db.query(ClienteModel).filter(ClienteModel.activo.is_(True)).count()

    return {
        "total_comentarios": total,
        "procesados": procesados,
        "positivos": positivos,
        "neutros": max(neutros, 0),
        "negativos": negativos,
        "promedio_polaridad": round(float(promedio), 4) if promedio else 0.0,
        "total_clientes": total_clientes,
    }


def _generar_csv(datos: dict, tipo: str) -> bytes:
    lineas = [
        f"Reporte: {tipo}",
        "",
        "INDICADOR,VALOR",
        f"Total Comentarios,{datos['total_comentarios']}",
        f"Procesados,{datos['procesados']}",
        f"Positivos,{datos['positivos']}",
        f"Neutros,{datos['neutros']}",
        f"Negativos,{datos['negativos']}",
        f"Polaridad Promedio,{datos['promedio_polaridad']}",
        f"Total Clientes,{datos['total_clientes']}",
    ]
    return "\n".join(lineas).encode("utf-8")


def _generar_pdf(datos: dict, tipo: str) -> bytes:
    """Genera un PDF válido estructurado en bajo nivel sin dependencias externas."""
    lineas_texto = [
        f"REPORTE: {tipo.upper()}",
        f"----------------------------------------",
        f"Total Comentarios : {datos['total_comentarios']}",
        f"Procesados        : {datos['procesados']}",
        f"Positivos         : {datos['positivos']}",
        f"Neutros           : {datos['neutros']}",
        f"Negativos         : {datos['negativos']}",
        f"Polaridad Promedio: {datos['promedio_polaridad']}",
        f"Total Clientes    : {datos['total_clientes']}",
    ]

    # Construcción de comandos PDF para texto multilínea
    pdf_cmds = ["BT", "/F1 12 Tf", "50 750 Td", "16 TL"]
    for i, line in enumerate(lineas_texto):
        # Escapar caracteres reservados de PDF
        line_clean = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            pdf_cmds.append(f"({line_clean}) Tj")
        else:
            pdf_cmds.append(f"T* ({line_clean}) Tj")
    pdf_cmds.append("ET")
    
    stream_content = "\n".join(pdf_cmds).encode("latin-1")

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        + f"4 0 obj\n<< /Length {len(stream_content)} >>\nstream\n".encode("latin-1")
        + stream_content
        + b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n%%EOF"
    )
    return pdf


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/general")
async def obtener_reporte_general(db: Session = Depends(get_db)):
    """Devuelve las métricas generales del sistema desde la BD real."""
    return JSONResponse(content=_datos_reporte(db))


@router.get("/exportar/pdf")
async def exportar_pdf(db: Session = Depends(get_db)):
    """Descarga un PDF con el reporte general."""
    datos = _datos_reporte(db)
    return Response(
        content=_generar_pdf(datos, "General"),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_general.pdf"},
    )


@router.post("/generar")
async def generar_reporte(
    payload: GenerarReportePayload,
    db: Session = Depends(get_db),
):
    """Genera y descarga un reporte según tipo y formato solicitado."""
    datos = _datos_reporte(db)
    fmt = payload.formato.upper()

    if fmt == "PDF":
        contenido = _generar_pdf(datos, payload.tipo)
        media_type = "application/pdf"
        extension = "pdf"
    elif fmt == "CSV":
        contenido = _generar_csv(datos, payload.tipo)
        media_type = "text/csv"
        extension = "csv"
    else:
        # Excel: fallback a CSV con extensión xlsx
        contenido = _generar_csv(datos, payload.tipo)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        extension = "xlsx"

    nombre = f"reporte_{payload.tipo.lower().replace(' ', '_')}.{extension}"
    return Response(
        content=contenido,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )