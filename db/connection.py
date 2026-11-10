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
    if "18456" in texto:
        return "Usuario o contraseña incorrectos."
    if "08001" in texto or "timeout" in texto.lower():
        return "No se pudo contactar al servidor. Revisa que SQL Server esté activo."
    return f"Error de conexión: {texto}"