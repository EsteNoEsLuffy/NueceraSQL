from collections import OrderedDict
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

import matplotlib
# "Agg" dibuja la grafica en memoria sin abrir ventanas; si no, matplotlib
# intenta abrir la suya y choca con la de PySide6
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)

# la carpeta queda junto al proyecto sin importar desde donde se ejecute la app
CARPETA_SALIDA = Path(__file__).resolve().parent.parent / "reportes_generados"
VERDE = colors.HexColor("#2E5E3E")


def obtener_ventas(conexion, fecha_inicio, fecha_fin):
    """Pide las ventas al procedimiento sp_ventas_por_fecha y de paso trae
    el nombre del usuario de SQL Server para ponerlo en el encabezado."""
    cursor = conexion.cursor()
    cursor.execute("{CALL sp_ventas_por_fecha (?, ?)}", fecha_inicio, fecha_fin)
    filas = cursor.fetchall()
    cursor.execute("SELECT SUSER_SNAME()")
    usuario = cursor.fetchone()[0]
    return filas, usuario


def _dinero(valor):
    # 1234.5 -> $1,234.50
    return f"${valor:,.2f}"


def _grafica_por_producto(totales):
    """Hace una grafica de barras con lo vendido por producto y la devuelve
    como imagen PNG en memoria (sin guardarla en disco) para meterla al PDF."""
    nombres = list(totales.keys())
    valores = [float(v) for v in totales.values()]

    figura, eje = plt.subplots(figsize=(7, 3.2), dpi=150)
    barras = eje.bar(nombres, valores, color="#2E5E3E")
    eje.set_title("Ventas por producto", fontsize=11)
    eje.set_ylabel("Total vendido ($)")
    # el monto arriba de cada barra
    eje.bar_label(barras, labels=[f"${v:,.0f}" for v in valores], fontsize=8)
    # quita las lineas de arriba y la derecha para que se vea mas limpia
    eje.spines[["top", "right"]].set_visible(False)
    plt.setp(eje.get_xticklabels(), fontsize=8)
    figura.tight_layout()

    imagen = BytesIO()
    figura.savefig(imagen, format="png")
    # cerrar la figura libera memoria; si no, se acumulan al generar varios reportes
    plt.close(figura)
    imagen.seek(0)
    return imagen


def generar_pdf(conexion, fecha_inicio: date, fecha_fin: date):
    """Genera el PDF y devuelve su ruta. Devuelve None si no hay ventas."""
    filas, usuario = obtener_ventas(conexion, fecha_inicio, fecha_fin)
    if not filas:
        return None

    CARPETA_SALIDA.mkdir(exist_ok=True)
    # el nombre lleva el rango; si se repite el mismo rango se sobreescribe
    ruta = CARPETA_SALIDA / f"ventas_{fecha_inicio}_a_{fecha_fin}.pdf"

    # estilos de texto del PDF; "celda" es una letra mas chica para las
    # tablas, para que los nombres largos hagan salto de linea
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=VERDE)
    normal = estilos["Normal"]
    celda = ParagraphStyle("celda", parent=normal, fontSize=8, leading=10)

    # hoja tamaño carta en horizontal, porque la tabla tiene muchas columnas
    doc = SimpleDocTemplate(str(ruta), pagesize=landscape(letter),
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title="Reporte de ventas", author="Nuecera")
    # reportlab arma el PDF con una lista de elementos que se acomodan en orden
    contenido = []

    # ---------- encabezado ----------
    contenido.append(Paragraph("Nuecera - Reporte de ventas", titulo))
    contenido.append(Paragraph(
        f"Periodo: <b>{fecha_inicio}</b> al <b>{fecha_fin}</b><br/>"
        f"Generado: {datetime.now():%Y-%m-%d %H:%M} por <b>{usuario}</b>", normal))
    contenido.append(Spacer(1, 0.5 * cm))

    # ---------- tabla de datos ----------
    # columnas que regresa el procedimiento: 0 id_venta, 1 fecha, 2 cliente,
    # 3 producto, 4 id_lote, 5 cantidad_kg, 6 precio_kg, 7 subtotal,
    # 8 total_venta, 9 usuario_bd (por eso abajo uso f[0], f[1], etc.)
    datos = [["Venta", "Fecha", "Cliente", "Producto", "Lote", "Kilos",
              "Precio/kg", "Subtotal", "Registró"]]
    for f in filas:
        datos.append([
            str(f[0]), f[1].strftime("%Y-%m-%d %H:%M"),
            Paragraph(str(f[2]), celda), Paragraph(str(f[3]), celda),
            str(f[4]), f"{f[5]:,.2f}", _dinero(f[6]), _dinero(f[7]),
            Paragraph(str(f[9] or ""), celda),
        ])

    # repeatRows=1 repite el encabezado en cada pagina si la tabla es larga
    tabla = Table(datos, repeatRows=1, colWidths=[
        1.4 * cm, 3.2 * cm, 5 * cm, 5 * cm, 1.4 * cm, 2.2 * cm,
        2.4 * cm, 2.8 * cm, 3.2 * cm])
    # los numeros entre parentesis son (columna, fila) de inicio y fin;
    # -1 significa "hasta el ultimo"
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        # kilos, precio y subtotal alineados a la derecha
        ("ALIGN", (5, 0), (7, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # filas alternando blanco y verde clarito para leer mejor
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3EF")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B8C4BA")),
    ]))
    contenido.append(tabla)
    contenido.append(Spacer(1, 0.5 * cm))

    # ---------- totales ----------
    total_kilos = sum(f[5] for f in filas)
    total_dinero = sum(f[7] for f in filas)
    # un set para no contar dos veces la misma venta
    num_ventas = len({f[0] for f in filas})

    resumen = Table([
        ["Número de ventas", str(num_ventas)],
        ["Total de kilos vendidos", f"{total_kilos:,.2f} kg"],
        ["TOTAL VENDIDO", _dinero(total_dinero)],
    ], colWidths=[6 * cm, 5 * cm], hAlign="RIGHT")
    resumen.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        # la ultima fila (el total) resaltada
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#DDE8DF")),
        ("LINEABOVE", (0, 2), (-1, 2), 0.8, VERDE),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B8C4BA")),
    ]))
    contenido.append(resumen)
    contenido.append(Spacer(1, 0.6 * cm))

    # ---------- gráfica ----------
    # suma los subtotales por nombre de producto (f[3] producto, f[7] subtotal)
    totales = OrderedDict()
    for f in filas:
        totales[str(f[3])] = totales.get(str(f[3]), 0) + f[7]
    contenido.append(Image(_grafica_por_producto(totales), width=16 * cm, height=7.3 * cm))

    doc.build(contenido)
    return ruta
