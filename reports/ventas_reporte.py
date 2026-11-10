from collections import OrderedDict
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # genera imágenes sin abrir ventanas (no choca con PySide6)
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)

CARPETA_SALIDA = Path(__file__).resolve().parent.parent / "reportes_generados"
VERDE = colors.HexColor("#2E5E3E")


def obtener_ventas(conexion, fecha_inicio, fecha_fin):
    """Llama al procedimiento almacenado sp_ventas_por_fecha."""
    cursor = conexion.cursor()
    cursor.execute("{CALL sp_ventas_por_fecha (?, ?)}", fecha_inicio, fecha_fin)
    filas = cursor.fetchall()
    cursor.execute("SELECT SUSER_SNAME()")
    usuario = cursor.fetchone()[0]
    return filas, usuario


def _dinero(valor):
    return f"${valor:,.2f}"


def _grafica_por_producto(totales):
    """Devuelve un PNG (en memoria) con las ventas totales por producto."""
    nombres = list(totales.keys())
    valores = [float(v) for v in totales.values()]

    figura, eje = plt.subplots(figsize=(7, 3.2), dpi=150)
    barras = eje.bar(nombres, valores, color="#2E5E3E")
    eje.set_title("Ventas por producto", fontsize=11)
    eje.set_ylabel("Total vendido ($)")
    eje.bar_label(barras, labels=[f"${v:,.0f}" for v in valores], fontsize=8)
    eje.spines[["top", "right"]].set_visible(False)
    plt.setp(eje.get_xticklabels(), fontsize=8)
    figura.tight_layout()

    imagen = BytesIO()
    figura.savefig(imagen, format="png")
    plt.close(figura)
    imagen.seek(0)
    return imagen


def generar_pdf(conexion, fecha_inicio: date, fecha_fin: date):
    """Genera el PDF y devuelve su ruta. Devuelve None si no hay ventas."""
    filas, usuario = obtener_ventas(conexion, fecha_inicio, fecha_fin)
    if not filas:
        return None

    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / f"ventas_{fecha_inicio}_a_{fecha_fin}.pdf"

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=VERDE)
    normal = estilos["Normal"]
    celda = ParagraphStyle("celda", parent=normal, fontSize=8, leading=10)

    doc = SimpleDocTemplate(str(ruta), pagesize=landscape(letter),
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title="Reporte de ventas", author="Nuecera")
    contenido = []

    # ---------- encabezado ----------
    contenido.append(Paragraph("Nuecera - Reporte de ventas", titulo))
    contenido.append(Paragraph(
        f"Periodo: <b>{fecha_inicio}</b> al <b>{fecha_fin}</b><br/>"
        f"Generado: {datetime.now():%Y-%m-%d %H:%M} por <b>{usuario}</b>", normal))
    contenido.append(Spacer(1, 0.5 * cm))

    # ---------- tabla de datos ----------
    # columnas del SP: 0 id_venta, 1 fecha, 2 cliente, 3 producto, 4 id_lote,
    # 5 cantidad_kg, 6 precio_kg, 7 subtotal, 8 total_venta, 9 usuario_bd
    datos = [["Venta", "Fecha", "Cliente", "Producto", "Lote", "Kilos",
              "Precio/kg", "Subtotal", "Registró"]]
    for f in filas:
        datos.append([
            str(f[0]), f[1].strftime("%Y-%m-%d %H:%M"),
            Paragraph(str(f[2]), celda), Paragraph(str(f[3]), celda),
            str(f[4]), f"{f[5]:,.2f}", _dinero(f[6]), _dinero(f[7]),
            Paragraph(str(f[9] or ""), celda),
        ])

    tabla = Table(datos, repeatRows=1, colWidths=[
        1.4 * cm, 3.2 * cm, 5 * cm, 5 * cm, 1.4 * cm, 2.2 * cm,
        2.4 * cm, 2.8 * cm, 3.2 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (5, 0), (7, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3EF")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B8C4BA")),
    ]))
    contenido.append(tabla)
    contenido.append(Spacer(1, 0.5 * cm))

    # ---------- totales ----------
    total_kilos = sum(f[5] for f in filas)
    total_dinero = sum(f[7] for f in filas)
    num_ventas = len({f[0] for f in filas})

    resumen = Table([
        ["Número de ventas", str(num_ventas)],
        ["Total de kilos vendidos", f"{total_kilos:,.2f} kg"],
        ["TOTAL VENDIDO", _dinero(total_dinero)],
    ], colWidths=[6 * cm, 5 * cm], hAlign="RIGHT")
    resumen.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#DDE8DF")),
        ("LINEABOVE", (0, 2), (-1, 2), 0.8, VERDE),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B8C4BA")),
    ]))
    contenido.append(resumen)
    contenido.append(Spacer(1, 0.6 * cm))

    # ---------- gráfica ----------
    totales = OrderedDict()
    for f in filas:
        totales[str(f[3])] = totales.get(str(f[3]), 0) + f[7]
    contenido.append(Image(_grafica_por_producto(totales), width=16 * cm, height=7.3 * cm))

    doc.build(contenido)
    return ruta