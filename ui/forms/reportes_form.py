import os
from datetime import date

import pyodbc
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    TitleLabel, BodyLabel, LineEdit, PrimaryPushButton, InfoBar, InfoBarPosition,
)

from reports.ventas_reporte import generar_pdf


class ReportesForm(QWidget):
    def __init__(self, conexion):
        super().__init__()
        self.setObjectName("reportes")
        self.conexion = conexion

        hoy = QDate.currentDate()
        self.fecha_inicio = LineEdit()
        self.fecha_inicio.setText(QDate(hoy.year(), 1, 1).toString("yyyy-MM-dd"))
        self.fecha_inicio.setPlaceholderText("AAAA-MM-DD")
        self.fecha_inicio.setMaxLength(10)
        self.fecha_fin = LineEdit()
        self.fecha_fin.setText(hoy.toString("yyyy-MM-dd"))
        self.fecha_fin.setPlaceholderText("AAAA-MM-DD")
        self.fecha_fin.setMaxLength(10)

        self.boton_generar = PrimaryPushButton("Generar PDF")
        self.boton_generar.clicked.connect(self.generar)

        fechas = QHBoxLayout()
        for etiqueta, campo in (("Desde", self.fecha_inicio), ("Hasta", self.fecha_fin)):
            columna = QVBoxLayout()
            columna.addWidget(BodyLabel(etiqueta))
            columna.addWidget(campo)
            fechas.addLayout(columna)
        fechas.addWidget(self.boton_generar)
        fechas.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.addWidget(TitleLabel("Reportes"))
        layout.addWidget(BodyLabel("Reporte de ventas por rango de fechas (PDF)."))
        layout.addLayout(fechas)
        layout.addStretch()

    def _aviso(self, tipo, titulo, mensaje):
        funcion = {"ok": InfoBar.success, "error": InfoBar.error,
                   "aviso": InfoBar.warning}[tipo]
        funcion(title=titulo, content=mensaje, parent=self,
                position=InfoBarPosition.TOP, duration=5000)

    @staticmethod
    def _fecha(texto):
        try:
            return date.fromisoformat(texto.strip())
        except ValueError:
            return None

    def generar(self):
        inicio = self._fecha(self.fecha_inicio.text())
        fin = self._fecha(self.fecha_fin.text())
        if inicio is None or fin is None:
            self._aviso("aviso", "Fecha inválida", "Usa el formato AAAA-MM-DD, ej. 2026-11-06.")
            return
        if inicio > fin:
            self._aviso("aviso", "Rango inválido", "La fecha inicial no puede ser mayor a la final.")
            return

        try:
            ruta = generar_pdf(self.conexion, inicio, fin)
        except pyodbc.Error as error:
            texto = str(error)
            if "permission was denied" in texto.lower() or "(229)" in texto:
                texto = "Tu usuario no tiene permiso para generar este reporte."
            self._aviso("error", "No se pudo generar", texto)
            return
        except PermissionError:
            self._aviso("error", "No se pudo guardar",
                        "Cierra el PDF si lo tienes abierto e inténtalo de nuevo.")
            return

        if ruta is None:
            self._aviso("aviso", "Sin ventas", "No hay ventas en ese rango de fechas.")
            return

        self._aviso("ok", "Reporte generado", f"Se guardó en reportes_generados/{ruta.name}")
        os.startfile(ruta)  # abre el PDF con el lector predeterminado de Windows