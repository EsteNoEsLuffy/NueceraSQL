from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from qfluentwidgets import SearchLineEdit


class BuscadorTabla:
    """Cuadro de busqueda para una tabla: oculta las filas que no contienen lo escrito.
    - Ctrl+F manda el cursor al cuadro desde cualquier parte de la pantalla
    - Enter selecciona la primera fila que coincide
    - Esc limpia la busqueda y regresa a la tabla
    La busqueda se hace sobre lo que ya esta en pantalla, no consulta la base."""

    def __init__(self, pagina, tabla, layout, placeholder="Buscar (Ctrl+F)"):
        self.tabla = tabla
        self.cuadro = SearchLineEdit()
        self.cuadro.setPlaceholderText(placeholder)
        self.cuadro.setClearButtonEnabled(True)
        self.cuadro.setFixedWidth(320)

        # se inserta justo arriba de la tabla (la tabla debe ser el ultimo widget del layout)
        layout.insertWidget(layout.indexOf(tabla), self.cuadro)

        self.cuadro.textChanged.connect(self.aplicar)
        self.cuadro.returnPressed.connect(self._ir_al_primero)

        atajo_buscar = QShortcut(QKeySequence.Find, pagina)
        atajo_buscar.setContext(Qt.WidgetWithChildrenShortcut)
        atajo_buscar.activated.connect(self._enfocar)

        atajo_limpiar = QShortcut(QKeySequence(Qt.Key_Escape), self.cuadro)
        atajo_limpiar.setContext(Qt.WidgetShortcut)
        atajo_limpiar.activated.connect(self._limpiar)

    def _enfocar(self):
        self.cuadro.setFocus()
        self.cuadro.selectAll()

    def _limpiar(self):
        self.cuadro.clear()
        self.tabla.setFocus()

    def aplicar(self):
        # se llama al escribir y tambien despues de recargar la tabla,
        # para que el filtro no se pierda al actualizar
        texto = self.cuadro.text().strip().lower()
        for fila in range(self.tabla.rowCount()):
            coincide = not texto
            if not coincide:
                for columna in range(self.tabla.columnCount()):
                    item = self.tabla.item(fila, columna)
                    if item and texto in item.text().lower():
                        coincide = True
                        break
            self.tabla.setRowHidden(fila, not coincide)

    def _ir_al_primero(self):
        for fila in range(self.tabla.rowCount()):
            if not self.tabla.isRowHidden(fila):
                self.tabla.selectRow(fila)
                self.tabla.setFocus()
                return
