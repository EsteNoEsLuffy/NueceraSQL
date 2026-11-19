import re
from pathlib import Path

import pyodbc

CARPETA = Path(__file__).parent / "scripts"
# primero los triggers y luego la carga del historial en la bitacora
SCRIPTS = ("04 Triggers.sql", "07_bitacora_historial.sql")


def _lotes_de_sql(texto):
    # SQL Server entiende "go" en SSMS pero no en pyodbc, asi que se separa el
    # archivo en bloques por cada linea que solo diga go
    bloques = re.split(r"^\s*go\s*$", texto, flags=re.IGNORECASE | re.MULTILINE)
    return [b.strip() for b in bloques if b.strip()]


def preparar_bitacora(conexion):
    """Crea (o actualiza) los triggers de la bitacora y carga lo que ya existia.
    Los scripts se pueden repetir sin problema (create or alter / not exists),
    asi que corre cada vez que entra alguien. Solo lo intenta un usuario con
    permisos de dueno de la base; para los demas no hace nada.
    Devuelve un texto con el error si algo fallo, o None si todo salio bien."""
    try:
        cursor = conexion.cursor()
        es_dueno = cursor.execute("SELECT IS_MEMBER('db_owner')").fetchone()[0]
        if not es_dueno:
            return None
        for nombre in SCRIPTS:
            texto = (CARPETA / nombre).read_text(encoding="utf-8")
            for bloque in _lotes_de_sql(texto):
                # el "use nuecera" sobra: la conexion ya esta en esa base
                if bloque.lower().startswith("use "):
                    continue
                cursor.execute(bloque)
                # algunos bloques (select) dejan resultados pendientes
                while cursor.nextset():
                    pass
        conexion.commit()
        return None
    except (pyodbc.Error, OSError) as error:
        try:
            conexion.rollback()
        except pyodbc.Error:
            pass
        return str(error)
