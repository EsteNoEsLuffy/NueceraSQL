from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF, TitleLabel, BodyLabel,
    InfoBar, InfoBarPosition,
)
from ui.forms.clientes_form import ClientesForm
from ui.forms.productores_form import ProductoresForm
from ui.forms.lotes_form import LotesForm
from ui.forms.inventario_form import InventarioForm
from ui.forms.ventas_form import VentasForm
from ui.forms.reportes_form import ReportesForm


class PaginaBase(QWidget):
    """Pagina de relleno que se uso mientras faltaban las pantallas reales.
    Ya no se usa en ningun lado, se puede borrar."""

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
    # FluentWindow ya trae el menu lateral; solo hay que registrarle las paginas
    def __init__(self, conexion, usuario):
        super().__init__()
        # La conexión queda guardada: todas las páginas la usarán
        self.conexion = conexion
        self.usuario = usuario

        # el nombre del usuario en el titulo ayuda a saber con quien se entro
        self.setWindowTitle(f"Nuecera - {usuario}")
        self.resize(1000, 650)

        # cada pantalla recibe la misma conexion y carga sus datos al crearse
        self.pagina_productores = ProductoresForm(conexion)
        self.pagina_lotes = LotesForm(conexion)
        self.pagina_inventario = InventarioForm(conexion)
        self.pagina_clientes = ClientesForm(conexion)
        self.pagina_ventas = VentasForm(conexion)
        self.pagina_reportes = ReportesForm(conexion)

        # el orden de abajo es el orden en que salen en el menu
        self.addSubInterface(self.pagina_productores, FIF.EDIT, "Productores")
        self.addSubInterface(self.pagina_lotes, FIF.TAG, "Lotes")
        self.addSubInterface(self.pagina_inventario, FIF.SHOPPING_CART, "Inventario")
        self.addSubInterface(self.pagina_clientes, FIF.PEOPLE, "Clientes")
        self.addSubInterface(self.pagina_ventas, FIF.DOCUMENT, "Ventas")
        # reportes se manda hasta abajo del menu
        self.addSubInterface(self.pagina_reportes, FIF.PRINT, "Reportes",
                             NavigationItemPosition.BOTTOM)
        # boton que no abre pagina (selectable=False), solo recarga las tablas.
        # Sirve cuando otro usuario hizo cambios y quiero verlos sin reiniciar
        self.navigationInterface.addItem(
            "actualizar_datos", FIF.SYNC, "Actualizar datos",
            onClick=self.actualizar_datos, selectable=False,
            position=NavigationItemPosition.TOP,
            tooltip="Recargar las tablas desde el servidor",
        )

    def actualizar_datos(self):
        # reportes no esta aqui porque no tiene tabla que recargar
        paginas = (
            self.pagina_productores,
            self.pagina_lotes,
            self.pagina_inventario,
            self.pagina_clientes,
            self.pagina_ventas,
        )
        # cargar() devuelve False si fallo; solo avisamos de exito si todas salieron bien
        resultados = [pagina.cargar() for pagina in paginas]
        if all(resultados):
            InfoBar.success(
                title="Datos actualizados",
                content="Las tablas se recargaron desde el servidor.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def closeEvent(self, evento):
        # Al cerrar la ventana, se cierra también la conexión a SQL Server
        try:
            self.conexion.close()
        except Exception:
            # si ya estaba cerrada o se cayo, no importa; igual cerramos la ventana
            pass
        super().closeEvent(evento)
