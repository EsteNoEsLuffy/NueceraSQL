from decimal import Decimal

import pyodbc
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from qfluentwidgets import (
    TitleLabel, PushButton, PrimaryPushButton, TableWidget, LineEdit, ComboBox,
    DateEdit, DoubleSpinBox, MessageBoxBase, SubtitleLabel, BodyLabel, MessageBox,
    InfoBar, InfoBarPosition,
)

from dao.lotes_dao import LotesDAO


class DialogoLote(MessageBoxBase):
    """Cuadro para capturar o editar un lote."""

    def __init__(self, parent, productores, productos, datos=None):
        super().__init__(parent)
        self.titulo = SubtitleLabel("Editar lote" if datos else "Nuevo lote")

        self.combo_productor = ComboBox()
        for id_, nombre in productores:
            self.combo_productor.addItem(nombre, userData=id_)
        self.combo_producto = ComboBox()
        for id_, nombre in productos:
            self.combo_producto.addItem(nombre, userData=id_)

        # Fecha como texto AAAA-MM-DD (hoy por defecto)
        self.fecha = LineEdit()
        self.fecha.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        self.fecha.setPlaceholderText("AAAA-MM-DD")
        self.fecha.setMaxLength(10)

        self.peso = LineEdit()
        self.peso.setPlaceholderText("Peso en kg, ej. 500.50")
        self.humedad = LineEdit()
        self.humedad.setPlaceholderText("Humedad %, ej. 4.2")
        self.precio = LineEdit()
        self.precio.setPlaceholderText("Precio de compra por kg, ej. 235")
        self.bodega = LineEdit()
        self.bodega.setPlaceholderText("Bodega")
        self.bodega.setMaxLength(50)

        if datos:
            self.combo_productor.setCurrentIndex(
                max(0, self.combo_productor.findData(datos["id_productor"])))
            self.combo_producto.setCurrentIndex(
                max(0, self.combo_producto.findData(datos["id_producto"])))
            self.fecha.setText(datos["fecha"])
            self.peso.setText(str(datos["peso"]))
            self.humedad.setText("" if datos["humedad"] is None else str(datos["humedad"]))
            self.precio.setText("" if datos["precio"] is None else str(datos["precio"]))
            self.bodega.setText(datos["bodega"])

        self.viewLayout.addWidget(self.titulo)
        for etiqueta, campo in (
            ("Productor", self.combo_productor), ("Producto", self.combo_producto),
            ("Fecha de recepción", self.fecha), ("Peso (kg)", self.peso),
            ("Humedad (%)", self.humedad), ("Precio de compra por kg", self.precio),
            ("Bodega", self.bodega),
        ):
            self.viewLayout.addWidget(BodyLabel(etiqueta))
            self.viewLayout.addWidget(campo)

        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(400)

    def _aviso(self, titulo, mensaje):
        InfoBar.warning(titulo, mensaje, parent=self,
                        position=InfoBarPosition.TOP, duration=3000)

    @staticmethod
    def _decimal(texto):
        """Convierte texto a Decimal; devuelve None si no es un número válido."""
        try:
            return Decimal(texto.strip().replace(",", ".")).quantize(Decimal("0.01"))
        except Exception:
            return None

    def validate(self):
        if self.combo_productor.currentData() is None:
            self._aviso("Falta productor", "Registra un productor primero.")
            return False
        if self.combo_producto.currentData() is None:
            self._aviso("Falta producto", "Registra un producto primero.")
            return False
        if not QDate.fromString(self.fecha.text().strip(), "yyyy-MM-dd").isValid():
            self._aviso("Fecha inválida", "Usa el formato AAAA-MM-DD, ej. 2026-11-06.")
            return False
        peso = self._decimal(self.peso.text())
        if peso is None or peso <= 0:
            self._aviso("Peso inválido", "El peso debe ser un número mayor a cero.")
            return False
        humedad = self._decimal(self.humedad.text())
        if humedad is None or not (0 <= humedad <= 100):
            self._aviso("Humedad inválida", "La humedad debe ser un número entre 0 y 100.")
            return False
        precio = self._decimal(self.precio.text())
        if precio is None or precio < 0:
            self._aviso("Precio inválido", "El precio debe ser un número, 0 o mayor.")
            return False
        return True

    def valores(self):
        bodega = self.bodega.text().strip()
        return (
            self.combo_productor.currentData(),
            self.combo_producto.currentData(),
            self.fecha.text().strip(),
            self._decimal(self.peso.text()),
            self._decimal(self.humedad.text()),
            self._decimal(self.precio.text()),
            bodega if bodega else None,
        )

class LotesForm(QWidget):
    COLUMNAS = ["ID", "Productor", "Producto", "Fecha", "Peso (kg)", "Humedad %",
                "Precio compra/kg", "Existencia (kg)", "Bodega"]

    def __init__(self, conexion):
        super().__init__()
        self.setObjectName("lotes")
        self.dao = LotesDAO(conexion)
        self.registros = []  # filas tal como vienen de la BD (incluyen los ids)

        self.boton_nuevo = PrimaryPushButton("Nuevo")
        self.boton_editar = PushButton("Editar")
        self.boton_eliminar = PushButton("Eliminar")
        self.boton_nuevo.clicked.connect(self.nuevo)
        self.boton_editar.clicked.connect(self.editar)
        self.boton_eliminar.clicked.connect(self.eliminar)

        self.tabla = TableWidget()
        self.tabla.setColumnCount(len(self.COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(self.COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().hide()
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        botones = QHBoxLayout()
        botones.addWidget(self.boton_nuevo)
        botones.addWidget(self.boton_editar)
        botones.addWidget(self.boton_eliminar)
        botones.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.addWidget(TitleLabel("Lotes"))
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.cargar()

    # ---------- utilidades ----------
    def _aviso(self, tipo, titulo, mensaje):
        funcion = {"ok": InfoBar.success, "error": InfoBar.error,
                   "aviso": InfoBar.warning}[tipo]
        funcion(title=titulo, content=mensaje, parent=self,
                position=InfoBarPosition.TOP, duration=4000)

    def _mensaje_error(self, error):
        texto = str(error)
        if "REFERENCE constraint" in texto:
            return "No se puede eliminar: este lote ya tiene ventas registradas."
        if "permission was denied" in texto.lower() or "(229)" in texto or "(230)" in texto:
            return "Tu usuario no tiene permiso para realizar esta acción."
        return f"Error de base de datos: {texto}"

    def _registro_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.registros):
            self._aviso("aviso", "Selecciona un lote", "Elige una fila de la tabla primero.")
            return None
        return self.registros[fila]

    def _listas(self):
        """Productores y productos para los desplegables."""
        try:
            return self.dao.productores(), self.dao.productos()
        except pyodbc.Error as error:
            self._aviso("error", "No se pudieron cargar las listas", self._mensaje_error(error))
            return None

    # ---------- operaciones ----------
    def cargar(self):
        try:
            self.registros = self.dao.listar()
        except pyodbc.Error as error:
            self._aviso("error", "No se pudo cargar", self._mensaje_error(error))
            return False
        self.tabla.setRowCount(len(self.registros))
        for i, fila in enumerate(self.registros):
            for j in range(len(self.COLUMNAS)):
                valor = fila[j]
                self.tabla.setItem(i, j, QTableWidgetItem("" if valor is None else str(valor)))
        return True

    def nuevo(self):
        listas = self._listas()
        if listas is None:
            return
        dialogo = DialogoLote(self.window(), *listas)
        if dialogo.exec():
            try:
                self.dao.insertar(*dialogo.valores())
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo guardar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Lote agregado", "Se guardó el lote y su inventario.")

    def editar(self):
        r = self._registro_seleccionado()
        if r is None:
            return
        listas = self._listas()
        if listas is None:
            return
        datos = {"id_productor": r[9], "id_producto": r[10], "fecha": str(r[3]),
                 "peso": r[4], "humedad": r[5], "precio": r[6], "bodega": r[8] or ""}
        dialogo = DialogoLote(self.window(), *listas, datos)
        if dialogo.exec():
            try:
                self.dao.actualizar(r[0], *dialogo.valores())
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo actualizar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Lote actualizado", "Los cambios se guardaron.")

    def eliminar(self):
        r = self._registro_seleccionado()
        if r is None:
            return
        confirmar = MessageBox("Eliminar lote",
                               f"¿Seguro que quieres eliminar el lote {r[0]} ({r[2]})?",
                               self.window())
        if confirmar.exec():
            try:
                self.dao.eliminar(r[0])
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo eliminar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Lote eliminado", "El lote y su inventario se eliminaron.")