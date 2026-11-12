import configparser
import pyodbc


class ErrorConexion(Exception):
    """Error al conectar, con un mensaje legible para mostrar en la interfaz."""


def _leer_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config["database"]


def conectar(usuario, contrasena):
    """Intenta conectarse a SQL Server con el usuario y contraseña dados.
    Si lo logra, devuelve la conexión; si falla, lanza ErrorConexion."""
    datos = _leer_config()
    cadena = (
        f"DRIVER={{{datos['driver']}}};"
        f"SERVER={datos['server']};"
        f"DATABASE={datos['database']};"
        f"UID={usuario};"
        f"PWD={contrasena};"
        "TrustServerCertificate=yes;"
    )
    try:
        return pyodbc.connect(cadena, timeout=5)
    except pyodbc.Error as error:
        raise ErrorConexion(_mensaje_amigable(error)) from error


def _mensaje_amigable(error):
    texto = str(error)
    texto_minusculas = texto.lower()
    if "18456" in texto:
        return "Usuario o contraseña incorrectos."
    if any(
        indicador in texto_minusculas
        for indicador in ("11001", "getaddrinfo failed", "no such host is known")
    ):
        return (
            "No se pudo resolver el nombre del servidor. Revisa la dirección en "
            "config.ini y prueba con la IP local y el puerto de SQL Server "
            "(por ejemplo, IP,1433)."
        )
    if "08001" in texto or "timeout" in texto_minusculas:
        return (
            "No se pudo contactar al servidor. Revisa que SQL Server esté activo, "
            "que TCP/IP esté habilitado y que el puerto esté permitido en el "
            f"firewall. Detalle técnico: {texto}"
        )
    return f"Error de conexión: {texto}"