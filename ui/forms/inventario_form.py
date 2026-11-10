import pyodbc
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from qfluentwidgets import (
    TitleLabel, PushButton, PrimaryPushButton, TableWidget, LineEdit,
    MessageBoxBase, SubtitleLabel, BodyLabel, InfoBar, InfoBarPosition,
)

from dao.inventario_dao import InventarioDAO


class DialogoBodega(MessageBoxBase):
    def __init__(self, parent, id_lote, bodega_actual):
        super().__init__(parent)
        self.viewLayout.addWidget(SubtitleLabel(f"Bodega del lote {id_lote}"))
        self.bodega = LineEdit()
        self.bodega.setPlaceholderText("Bodega")
        self.bodega.setMaxLength(50)
        self.bodega.setText(bodega_actual)
        self.viewLayout.addWidget(BodyLabel("Bodega"))
        self.viewLayout.addWidget(self.bodega)
        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(340)

    def valor(self):
        texto = self.bodega.text().strip()
        return texto if texto else None


class InventarioForm(QWidget):
    COLUMNAS = ["Lote", "Producto", "Productor", "Existencia (kg)", "Bodega"]

    def __init__(self, conexion):
        super().__init__()
        self.setObjectName("inventario")
        self.dao = InventarioDAO(conexion)

        self.boton_bodega = PrimaryPushButton("Editar bodega")
        self.boton_actualizar = PushButton("Actualizar")
        self.boton_bodega.clicked.connect(self.editar_bodega)
        self.boton_actualizar.clicked.connect(self.cargar)

        self.tabla = TableWidget()
        self.tabla.setColumnCount(len(self.COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(self.COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().hide()
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        botones = QHBoxLayout()
        botones.addWidget(self.boton_bodega)
        botones.addWidget(self.boton_actualizar)
        botones.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.addWidget(TitleLabel("Inventario"))
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.cargar()

    def _aviso(self, tipo, titulo, mensaje):
        funcion = {"ok": InfoBar.success, "error": InfoBar.error,
                   "aviso": InfoBar.warning}[tipo]
        funcion(title=titulo, content=mensaje, parent=self,
                position=InfoBarPosition.TOP, duration=4000)

    def _mensaje_error(self, error):
        texto = str(error)
        if "permission was denied" in texto.lower() or "(229)" in texto or "(230)" in texto:
            return "Tu usuario no tiene permiso para realizar esta acción."
        return f"Error de base de datos: {texto}"

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

    def editar_bodega(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            self._aviso("aviso", "Selecciona un lote", "Elige una fila de la tabla primero.")
            return
        id_lote = int(self.tabla.item(fila, 0).text())
        actual = self.tabla.item(fila, 4).text() if self.tabla.item(fila, 4) else ""
        dialogo = DialogoBodega(self.window(), id_lote, actual)
        if dialogo.exec():
            try:
                self.dao.cambiar_bodega(id_lote, dialogo.valor())
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo actualizar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Bodega actualizada", "El cambio se guardó.")
            