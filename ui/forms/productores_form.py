import pyodbc
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from qfluentwidgets import (
    TitleLabel, PushButton, PrimaryPushButton, TableWidget, LineEdit,
    MessageBoxBase, SubtitleLabel, MessageBox, InfoBar, InfoBarPosition,
)

from dao.productores_dao import ProductoresDAO
from ui.buscador import BuscadorTabla


class DialogoProductor(MessageBoxBase):
    """Cuadro para capturar o editar un productor. Funciona igual que el de
    clientes: con datos es edicion, sin datos es registro nuevo."""

    def __init__(self, parent, datos=None):
        super().__init__(parent)
        self.titulo = SubtitleLabel("Editar productor" if datos else "Nuevo productor")

        # los maximos de caracteres son los mismos que los nvarchar de la tabla,
        # asi la base no recibe texto que no le cabe
        self.nombre = LineEdit()
        self.nombre.setPlaceholderText("Nombre (obligatorio)")
        self.nombre.setMaxLength(50)
        self.telefono = LineEdit()
        self.telefono.setPlaceholderText("Teléfono")
        self.telefono.setMaxLength(20)
        self.huerta = LineEdit()
        self.huerta.setPlaceholderText("Huerta")
        self.huerta.setMaxLength(100)
        self.ubicacion = LineEdit()
        self.ubicacion.setPlaceholderText("Ubicación")
        self.ubicacion.setMaxLength(150)

        if datos:
            self.nombre.setText(datos["nombre"])
            self.telefono.setText(datos["telefono"])
            self.huerta.setText(datos["huerta"])
            self.ubicacion.setText(datos["ubicacion"])

        self.viewLayout.addWidget(self.titulo)
        for campo in (self.nombre, self.telefono, self.huerta, self.ubicacion):
            self.viewLayout.addWidget(campo)

        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
        self.widget.setMinimumWidth(380)

    def validate(self):
        # el cuadro no se cierra mientras esto devuelva False
        if not self.nombre.text().strip():
            InfoBar.warning("Falta el nombre", "El nombre es obligatorio.",
                            parent=self, position=InfoBarPosition.TOP, duration=3000)
            return False
        return True

    def valores(self):
        # lo opcional que se deje vacio se manda como NULL
        def o_nulo(texto):
            texto = texto.strip()
            return texto if texto else None
        return (self.nombre.text().strip(), o_nulo(self.telefono.text()),
                o_nulo(self.huerta.text()), o_nulo(self.ubicacion.text()))


class ProductoresForm(QWidget):
    COLUMNAS = ["ID", "Nombre", "Teléfono", "Huerta", "Ubicación"]

    def __init__(self, conexion):
        super().__init__()
        self.setObjectName("productores")
        self.dao = ProductoresDAO(conexion)

        self.boton_nuevo = PrimaryPushButton("Nuevo")
        self.boton_editar = PushButton("Editar")
        self.boton_eliminar = PushButton("Eliminar")
        self.boton_nuevo.clicked.connect(self.nuevo)
        self.boton_editar.clicked.connect(self.editar)
        self.boton_eliminar.clicked.connect(self.eliminar)

        # tabla solo de lectura, se selecciona la fila completa
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
        layout.addWidget(TitleLabel("Productores"))
        layout.addLayout(botones)
        layout.addWidget(self.tabla)
        self.busqueda = BuscadorTabla(self, self.tabla, layout)

        self.cargar()

    # ---------- utilidades ----------
    def _aviso(self, tipo, titulo, mensaje):
        funcion = {"ok": InfoBar.success, "error": InfoBar.error,
                   "aviso": InfoBar.warning}[tipo]
        funcion(title=titulo, content=mensaje, parent=self,
                position=InfoBarPosition.TOP, duration=4000)

    def _mensaje_error(self, error):
        texto = str(error)
        # Primero la llave foránea (547), porque su nombre puede contener cualquier número
        if "REFERENCE constraint" in texto or "(547)" in texto:
            return "No se puede eliminar: este productor tiene lotes registrados."
        if "permission was denied" in texto.lower() or "(229)" in texto or "(230)" in texto:
            return "Tu usuario no tiene permiso para realizar esta acción."
        return f"Error de base de datos: {texto}"

    def _fila_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            self._aviso("aviso", "Selecciona un productor", "Elige una fila de la tabla primero.")
            return None
        return fila

    def _texto(self, fila, columna):
        item = self.tabla.item(fila, columna)
        return item.text() if item else ""

    # ---------- operaciones ----------
    def cargar(self):
        # recarga la tabla desde la base; False si algo fallo
        try:
            filas = self.dao.listar()
        except pyodbc.Error as error:
            self._aviso("error", "No se pudo cargar", self._mensaje_error(error))
            return False
        self.tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                self.tabla.setItem(i, j, QTableWidgetItem("" if valor is None else str(valor)))
        self.busqueda.aplicar()
        return True

    def nuevo(self):
        dialogo = DialogoProductor(self.window())
        if dialogo.exec():
            try:
                self.dao.insertar(*dialogo.valores())
            except pyodbc.Error as error:
                # el rollback deja la conexion lista para la siguiente operacion
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo guardar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Productor agregado", "El registro se guardó correctamente.")

    def editar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_productor = int(self._texto(fila, 0))
        datos = {"nombre": self._texto(fila, 1), "telefono": self._texto(fila, 2),
                 "huerta": self._texto(fila, 3), "ubicacion": self._texto(fila, 4)}
        dialogo = DialogoProductor(self.window(), datos)
        if dialogo.exec():
            try:
                self.dao.actualizar(id_productor, *dialogo.valores())
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo actualizar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Productor actualizado", "Los cambios se guardaron.")

    def eliminar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_productor = int(self._texto(fila, 0))
        nombre = self._texto(fila, 1)
        confirmar = MessageBox("Eliminar productor",
                               f"¿Seguro que quieres eliminar a «{nombre}»?", self.window())
        if confirmar.exec():
            try:
                self.dao.eliminar(id_productor)
            except pyodbc.Error as error:
                self.dao.conexion.rollback()
                self._aviso("error", "No se pudo eliminar", self._mensaje_error(error))
                return
            self.cargar()
            self._aviso("ok", "Productor eliminado", "El registro se eliminó.")
