class ProductoresDAO:
    """Acceso a la tabla productores, con la conexión del usuario en sesión."""

    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
        cursor.execute(
            "SELECT id_productor, nombre, telefono, huerta, ubicacion "
            "FROM productores ORDER BY nombre"
        )
        return cursor.fetchall()

    def insertar(self, nombre, telefono, huerta, ubicacion):
        cursor = self.conexion.cursor()
        cursor.execute(
            "INSERT INTO productores (nombre, telefono, huerta, ubicacion) "
            "VALUES (?, ?, ?, ?)",
            nombre, telefono, huerta, ubicacion,
        )
        self.conexion.commit()

    def actualizar(self, id_productor, nombre, telefono, huerta, ubicacion):
        cursor = self.conexion.cursor()
        cursor.execute(
            "UPDATE productores SET nombre = ?, telefono = ?, huerta = ?, ubicacion = ? "
            "WHERE id_productor = ?",
            nombre, telefono, huerta, ubicacion, id_productor,
        )
        self.conexion.commit()

    def eliminar(self, id_productor):
        cursor = self.conexion.cursor()
        cursor.execute("DELETE FROM productores WHERE id_productor = ?", id_productor)
        self.conexion.commit()