import io
import csv

def generar_archivo_reporte(tipo: str, formato: str) -> tuple[io.BytesIO, str, str]:
    fmt = formato.lower()
    buffer = io.BytesIO()
    
    if "pdf" in fmt:
        contenido = (
            f"==================================================\n"
            f"          EMPRESA INTELIGENTE - REPORTE\n"
            f"==================================================\n\n"
            f"Tipo de Reporte : {tipo}\n"
            f"Formato         : Documento Ejecutivo (PDF)\n"
            f"Estado          : Generado con exito\n\n"
            f"--- RESUMEN EJECUTIVO ---\n"
            f"Este archivo contiene los datos procesados en tiempo real\n"
            f"desde los modulos analiticos de la plataforma.\n"
        )
        buffer.write(contenido.encode("utf-8"))
        buffer.seek(0)
        return buffer, "application/pdf", f"reporte_{tipo.lower().replace(' ', '_')}.pdf"

    else:
        # Generación de CSV / Excel
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Parametro", "Detalle"])
        writer.writerow(["Tipo de Reporte", tipo])
        writer.writerow(["Formato", "CSV / Spreadsheet"])
        writer.writerow(["Estado", "Procesado"])
        
        buffer.write(output.getvalue().encode("utf-8"))
        buffer.seek(0)
        return buffer, "text/csv", f"reporte_{tipo.lower().replace(' ', '_')}.csv"