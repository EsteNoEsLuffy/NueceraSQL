import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

from ui.login import VentanaLogin
from ui.main_window import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    setTheme(Theme.AUTO)

    login = VentanaLogin()
    ventanas = {}  # guarda la ventana principal para que no la elimine Python

    def al_entrar(conexion, usuario):
        ventanas["principal"] = VentanaPrincipal(conexion, usuario)
        ventanas["principal"].show()
        login.close()

    login.acceso_concedido.connect(al_entrar)
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()