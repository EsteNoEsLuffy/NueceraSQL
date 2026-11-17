import configparser
import pyodbc


class ErrorConexion(Exception):
    """Error al conectar. Trae un mensaje que ya se puede mostrar al usuario."""


def _leer_config():
    # lee el servidor, la base y el driver del config.ini
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config["database"]


def conectar(usuario, contrasena):
    """Abre la conexion a SQL Server con el usuario que escribio en el login.
    Como cada quien entra con su propio usuario de SQL Server, los permisos
    (quien puede insertar, borrar, etc.) los decide la base de datos, no la app.
    Si algo falla lanza ErrorConexion."""
    datos = _leer_config()
    cadena = (
        f"DRIVER={{{datos['driver']}}};"
        f"SERVER={datos['server']};"
        f"DATABASE={datos['database']};"
        f"UID={usuario};"
        f"PWD={contrasena};"
        # el driver 18 exige certificado valido; con esto aceptamos el que trae
        # el servidor local de pruebas
        "TrustServerCertificate=yes;"
    )
    try:
        # timeout de 5 segundos para que no se quede congelado si no hay servidor
        return pyodbc.connect(cadena, timeout=5)
    except pyodbc.Error as error:
        raise ErrorConexion(_mensaje_amigable(error)) from error


def _mensaje_amigable(error):
    """Cambia los errores tecnicos del driver por algo que se entienda."""
    texto = str(error)
    texto_minusculas = texto.lower()
    # 18456 es el codigo de SQL Server para login fallido
    if "18456" in texto:
        return "Usuario o contraseña incorrectos."
    # errores de DNS: el nombre del servidor no existe o esta mal escrito
    if any(
        indicador in texto_minusculas
        for indicador in ("11001", "getaddrinfo failed", "no such host is known")
    ):
        return (
            "No se pudo resolver el nombre del servidor. Revisa la dirección en "
            "config.ini y prueba con la IP local y el puerto de SQL Server "
            "(por ejemplo, IP,1433)."
        )
    # no hubo respuesta: servidor apagado, TCP/IP deshabilitado o firewall
    if "08001" in texto or "timeout" in texto_minusculas:
        return (
            "No se pudo contactar al servidor. Revisa que SQL Server esté activo, "
            "que TCP/IP esté habilitado y que el puerto esté permitido en el "
            f"firewall. Detalle técnico: {texto}"
        )
    return f"Error de conexión: {texto}"
