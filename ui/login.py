from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    LineEdit, PasswordLineEdit, PrimaryPushButton,
    TitleLabel, BodyLabel, InfoBar, InfoBarPosition,
)

from db.connection import conectar, ErrorConexion


class VentanaLogin(QWidget):
    # Señal que se emite cuando el login es correcto.
    # Lleva la conexión y el nombre de usuario.
    acceso_concedido = Signal(object, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nuecera - Iniciar sesión")
        self.setFixedSize(380, 340)

        titulo = TitleLabel("Nuecera")
        titulo.setAlignment(Qt.AlignCenter)
        subtitulo = BodyLabel("Inicia sesión con tu usuario de SQL Server")
        subtitulo.setAlignment(Qt.AlignCenter)

        self.campo_usuario = LineEdit()
        self.campo_usuario.setPlaceholderText("Usuario")
        self.campo_usuario.setClearButtonEnabled(True)

        self.campo_contrasena = PasswordLineEdit()
        self.campo_contrasena.setPlaceholderText("Contraseña")

        self.boton_entrar = PrimaryPushButton("Entrar")
        self.boton_entrar.clicked.connect(self.intentar_login)
        # Enter en el campo de contraseña también intenta entrar
        self.campo_contrasena.returnPressed.connect(self.intentar_login)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(14)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addSpacing(10)
        layout.addWidget(self.campo_usuario)
        layout.addWidget(self.campo_contrasena)
        layout.addSpacing(6)
        layout.addWidget(self.boton_entrar)

    def intentar_login(self):
        usuario = self.campo_usuario.text().strip()
        contrasena = self.campo_contrasena.text()

        if not usuario or not contrasena:
            self._aviso_error("Faltan datos", "Escribe usuario y contraseña.")
            return

        try:
            conexion = conectar(usuario, contrasena)
        except ErrorConexion as error:
            self._aviso_error("No se pudo entrar", str(error))
            return

        self.acceso_concedido.emit(conexion, usuario)

    def _aviso_error(self, titulo, mensaje):
        InfoBar.error(
            title=titulo,
            content=mensaje,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=4000,
        )