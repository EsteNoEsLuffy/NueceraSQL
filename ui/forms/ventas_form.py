from decimal import Decimal

import pyodbc
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from qfluentwidgets import (
    TitleLabel, PushButton, PrimaryPushButton, TableWidget, LineEdit, ComboBox,
    MessageBoxBase, MessageBox, SubtitleLabel, BodyLabel, InfoBar, InfoBarPosition,
)

from dao.ventas_dao import VentasDAO


class DialogoVenta(MessageBoxBase):
    def __init__(self, parent, clientes, lotes):
        super().__init__(parent)
        self.lotes = {l[0]: l for l in lotes}  # id_lote -> fila

        self.combo_cliente = ComboBox()
        for id_, nombre in clientes:
            self.combo_cliente.addItem(nombre, userData=id_)

        self.combo_lote = ComboBox()
        for id_lote, producto, existencia, _precio in lotes:
            self.combo_lote.addItem(f"Lote {id_lote} - {producto} ({existencia} kg)",
                                    userData=id_lote)
        self.combo_lote.currentIndexChanged.connect(self._sugerir_precio)

        self.cantidad = LineEdit()
        self.cantidad.setPlaceholderText("Cantidad en kg, ej. 100")
        self.precio = LineEdit()
        self.precio.setPlaceholderText("Precio por kg")
        self._sugerir_precio()

        self.viewLayout.addWidget(SubtitleLabel("Registrar venta"))
        for etiqueta, campo in (("Cliente", self.combo_cliente), ("Lote", self.combo_lote),
                                ("Cantidad (kg)", self.cantidad),
                                ("Precio por kg", self.precio)):
            self.viewLayout.addWidget(BodyLabel(etiqueta))
            self.viewLayout.addWidget(campo)

        self.yesButton.setText("Registrar")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(400)

    def _sugerir_precio(self):
        fila = self.lotes.get(self.combo_lote.currentData())
        if fila:
            self.precio.setText(str(fila[3]))

    def _aviso(self, titulo, mensaje):
        InfoBar.warning(titulo, mensaje, parent=self,
                        position=InfoBarPosition.TOP, duration=3000)

    @staticmethod
    def _decimal(texto):
        try:
            return Decimal(texto.strip().replace(",", ".")).quantize(Decimal("0.01"))
        except Exception:
            return None

    def validate(self):
        if self.combo_cliente.currentData() is None:
            self._aviso("Falta cliente", "Registra un cliente primero.")
            return False
        if self.combo_lote.currentData() is None:
            self._aviso("Sin existencias", "No hay lotes con existencia para vender.")
            return False
        cantidad = self._decimal(self.cantidad.text())
        if cantidad is None or cantidad <= 0:
            self._aviso("Cantidad inválida", "La cantidad debe ser mayor a cero.")
            return False
        # Valida la existencia aquí, antes de llamar a SQL Server
        fila = self.lotes.get(self.combo_lote.currentData())
        if fila and cantidad > fila[2]:
            self._aviso("Existencia insuficiente",
                        f"El lote {fila[0]} solo tiene {fila[2]} kg disponibles.")
            return False
        precio = self._decimal(self.precio.text())
        if precio is None or precio <= 0:
            self._aviso("Precio inválido", "El precio debe ser mayor a cero.")
            return False
        return True

    def valores(self):
        return (self.combo_cliente.currentData(), self.combo_lote.currentData(),
                self._decimal(self.cantidad.text()), self._decimal(self.precio.text()))


class VentasForm(QWidget):
    COLUMNAS = ["Venta", "Fecha", "Cliente", "Producto", "Lote", "Kilos",
                "Precio/kg", "Subtotal", "Total venta", "Registró"]

    def __init__(self, conexion):
        super().__init__()
        self.setObjectName("ventas")
        self.dao = VentasDAO(conexion)

        self.boton_registrar = PrimaryPushButton("Registrar venta")
        self.boton_actualizar = PushButton("Actualizar")
        self.boton_anular = PushButton("Anular venta")
        self.boton_registrar.clicked.connect(self.registrar)
        self.boton_actualizar.clicked.connect(self.cargar)
        self.boton_anular.clicked.connect(self.anular)

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
        botones.addWidget(self.boton_registrar)
        botones.addWidget(self.boton_actualizar)
        botones.addWidget(self.boton_anular)
        botones.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.addWidget(TitleLabel("Ventas"))
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.cargar()

    # ---------- utilidades ----------
    def _aviso(self, tipo, titulo, mensaje):
        funcion = {"ok": InfoBar.success, "error": InfoBar.error,
                   "aviso": InfoBar.warning}[tipo]
        funcion(title=titulo, content=mensaje, parent=self,
                position=InfoBarPosition.TOP, duration=5000)

    def _mensaje_error(self, error):
        texto = str(error)
        if "permission was denied" in texto.lower() or "(229)" in texto or "(230)" in texto:
            return "Tu usuario no tiene permiso para realizar esta acción."
        # Mensajes de los procedimientos (raiserror): se muestran tal cual
        for mensaje in ("la cantidad debe ser mayor a cero", "el cliente no existe",
                        "el lote no existe en inventario",
                        "no hay suficiente existencia en el lote",
                        "la venta no existe"):
            if mensaje in texto:
                return mensaje.capitalize() + "."
        # Muestra solo el último fragmento del mensaje, sin el ruido del driver
        limpio = texto.split("]")[-1].strip(" )'\"")
        return "Error de base de datos: " + limpio

    # ---------- operaciones ----------
    def cargar(self):
        try:
            filas = self.dao.listar()
        except pyodbc.Error as error:
            self._aviso("error", "No se pudo cargar", self._mensaje_error(error))
            return
        self.tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                self.tabla.setItem(i, j, QTableWidgetItem("" if valor is None else str(valor)))

    def registrar(self):
        try:
            clientes = self.dao.clientes()
            lotes = self.dao.lotes_disponibles()
        except pyodbc.Error as error:
            self._aviso("error", "No se pudieron cargar las listas", self._mensaje_error(error))
            return
        dialogo = DialogoVenta(self.window(), clientes, lotes)
        if dialogo.exec():
            try:
                id_venta = self.dao.registrar(*dialogo.valores())
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo registrar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Venta registrada", f"Venta número {id_venta} guardada.")

    def anular(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            self._aviso("aviso", "Selecciona una venta", "Elige una fila de la tabla primero.")
            return
        id_venta = int(self.tabla.item(fila, 0).text())
        total = self.tabla.item(fila, 8).text()
        confirmar = MessageBox(
            "Anular venta",
            f"¿Anular la venta {id_venta} por ${total}?\n"
            "Los kilos regresarán al inventario.", self.window())
        if confirmar.exec():
            try:
                self.dao.anular(id_venta)
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo anular", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Venta anulada",
                        f"La venta {id_venta} se anuló y el inventario se repuso.")