import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

from ui.login import VentanaLogin
from ui.main_window import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    # el tema (claro u oscuro) se toma del que tenga configurado Windows
    setTheme(Theme.AUTO)

    login = VentanaLogin()
    # Guardo la ventana principal en un diccionario porque si solo vive en una
    # variable local de al_entrar, Python la borra al terminar la funcion
    # y la ventana desaparece en cuanto aparece
    ventanas = {}

    def al_entrar(conexion, usuario):
        ventanas["principal"] = VentanaPrincipal(conexion, usuario)
        ventanas["principal"].show()
        login.close()

    # cuando el login sale bien, abrimos la app y cerramos la pantalla de login
    login.acceso_concedido.connect(al_entrar)
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
