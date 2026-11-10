from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF, TitleLabel, BodyLabel,
)
from ui.forms.clientes_form import ClientesForm
from ui.forms.productores_form import ProductoresForm
from ui.forms.lotes_form import LotesForm
from ui.forms.inventario_form import InventarioForm
from ui.forms.ventas_form import VentasForm
from ui.forms.reportes_form import ReportesForm


class PaginaBase(QWidget):
    """Página provisional: solo muestra el título de la sección."""

    def __init__(self, clave, titulo):
        super().__init__()
        # objectName es obligatorio: el menú lo usa para identificar cada página
        self.setObjectName(clave)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(TitleLabel(titulo))
        layout.addWidget(BodyLabel("Aquí irá el contenido de esta sección."))
        layout.addStretch()


class VentanaPrincipal(FluentWindow):
    def __init__(self, conexion, usuario):
        super().__init__()
        # La conexión queda guardada: todas las páginas la usarán
        self.conexion = conexion
        self.usuario = usuario

        self.setWindowTitle(f"Nuecera - {usuario}")
        self.resize(1000, 650)

        self.pagina_productores = ProductoresForm(conexion)
        self.pagina_lotes = LotesForm(conexion)
        self.pagina_inventario = InventarioForm(conexion)
        self.pagina_clientes = ClientesForm(conexion)
        self.pagina_ventas = VentasForm(conexion)
        self.pagina_reportes = ReportesForm(conexion)

        self.addSubInterface(self.pagina_productores, FIF.EDIT, "Productores")
        self.addSubInterface(self.pagina_lotes, FIF.TAG, "Lotes")
        self.addSubInterface(self.pagina_inventario, FIF.SHOPPING_CART, "Inventario")
        self.addSubInterface(self.pagina_clientes, FIF.PEOPLE, "Clientes")
        self.addSubInterface(self.pagina_ventas, FIF.DOCUMENT, "Ventas")
        self.addSubInterface(self.pagina_reportes, FIF.PRINT, "Reportes",
                             NavigationItemPosition.BOTTOM)

    def closeEvent(self, evento):
        # Al cerrar la ventana, se cierra también la conexión a SQL Server
        try:
            self.conexion.close()
        except Exception:
            pass
        super().closeEvent(evento)