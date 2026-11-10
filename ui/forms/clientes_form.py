import pyodbc
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from qfluentwidgets import (
    TitleLabel, PushButton, PrimaryPushButton, TableWidget, LineEdit,
    MessageBoxBase, SubtitleLabel, MessageBox, InfoBar, InfoBarPosition,
)

from dao.clientes_dao import ClientesDAO


class DialogoCliente(MessageBoxBase):
    """Cuadro para capturar o editar un cliente."""

    def __init__(self, parent, datos=None):
        super().__init__(parent)
        self.titulo = SubtitleLabel("Editar cliente" if datos else "Nuevo cliente")

        self.nombre = LineEdit()
        self.nombre.setPlaceholderText("Nombre (obligatorio)")
        self.telefono = LineEdit()
        self.telefono.setPlaceholderText("Teléfono")
        self.correo = LineEdit()
        self.correo.setPlaceholderText("Correo")
        self.direccion = LineEdit()
        self.direccion.setPlaceholderText("Dirección")

        if datos:
            self.nombre.setText(datos["nombre"])
            self.telefono.setText(datos["telefono"])
            self.correo.setText(datos["correo"])
            self.direccion.setText(datos["direccion"])

        self.viewLayout.addWidget(self.titulo)
        for campo in (self.nombre, self.telefono, self.correo, self.direccion):
            self.viewLayout.addWidget(campo)

        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(380)

    def validate(self):
        # Se ejecuta al pulsar Guardar; si devuelve False, el cuadro no se cierra
        if not self.nombre.text().strip():
            InfoBar.warning("Falta el nombre", "El nombre es obligatorio.",
                            parent=self, position=InfoBarPosition.TOP, duration=3000)
            return False
        return True

    def valores(self):
        # Los campos opcionales vacíos se guardan como NULL
        def o_nulo(texto):
            texto = texto.strip()
            return texto if texto else None
        return (self.nombre.text().strip(), o_nulo(self.telefono.text()),
                o_nulo(self.correo.text()), o_nulo(self.direccion.text()))


class ClientesForm(QWidget):
    COLUMNAS = ["ID", "Nombre", "Teléfono", "Correo", "Dirección"]

    def __init__(self, conexion):
        super().__init__()
        self.setObjectName("clientes")
        self.dao = ClientesDAO(conexion)

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
        self.tabla.setColumnWidth(0, 60)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        botones = QHBoxLayout()
        botones.addWidget(self.boton_nuevo)
        botones.addWidget(self.boton_editar)
        botones.addWidget(self.boton_eliminar)
        botones.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.addWidget(TitleLabel("Clientes"))
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
        if "permission was denied" in texto.lower() or "229" in texto or "230" in texto:
            return "Tu usuario no tiene permiso para realizar esta acción."
        if "REFERENCE constraint" in texto or "547" in texto:
            return "No se puede eliminar: este cliente tiene ventas registradas."
        return f"Error de base de datos: {texto}"

    def _fila_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            self._aviso("aviso", "Selecciona un cliente", "Elige una fila de la tabla primero.")
            return None
        return fila

    def _texto(self, fila, columna):
        item = self.tabla.item(fila, columna)
        return item.text() if item else ""

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

    def nuevo(self):
        dialogo = DialogoCliente(self.window())
        if dialogo.exec():
            try:
                self.dao.insertar(*dialogo.valores())
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo guardar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Cliente agregado", "El registro se guardó correctamente.")

    def editar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_cliente = int(self._texto(fila, 0))
        datos = {"nombre": self._texto(fila, 1), "telefono": self._texto(fila, 2),
                 "correo": self._texto(fila, 3), "direccion": self._texto(fila, 4)}
        dialogo = DialogoCliente(self.window(), datos)
        if dialogo.exec():
            try:
                self.dao.actualizar(id_cliente, *dialogo.valores())
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo actualizar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Cliente actualizado", "Los cambios se guardaron.")

    def eliminar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_cliente = int(self._texto(fila, 0))
        nombre = self._texto(fila, 1)
        confirmar = MessageBox("Eliminar cliente",
                               f"¿Seguro que quieres eliminar a «{nombre}»?", self.window())
        if confirmar.exec():
            try:
                self.dao.eliminar(id_cliente)
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo eliminar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Cliente eliminado", "El registro se eliminó.")