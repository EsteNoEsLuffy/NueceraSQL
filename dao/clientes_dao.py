class ClientesDAO:
    """Acceso a la tabla clientes. Recibe la conexión del usuario que inició sesión,
    así que SQL Server aplica sus permisos en cada operación."""

    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
        cursor.execute(
            "SELECT id_cliente, nombre, telefono, correo, direccion "
            "FROM clientes ORDER BY nombre"
        )
        return cursor.fetchall()

    def insertar(self, nombre, telefono, correo, direccion):
        cursor = self.conexion.cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, correo, direccion) "
            "VALUES (?, ?, ?, ?)",
            nombre, telefono, correo, direccion,
        )
        self.conexion.commit()

    def actualizar(self, id_cliente, nombre, telefono, correo, direccion):
        cursor = self.conexion.cursor()
        cursor.execute(
            "UPDATE clientes SET nombre = ?, telefono = ?, correo = ?, direccion = ? "
            "WHERE id_cliente = ?",
            nombre, telefono, correo, direccion, id_cliente,
        )
        self.conexion.commit()

    def eliminar(self, id_cliente):
        cursor = self.conexion.cursor()
        cursor.execute("DELETE FROM clientes WHERE id_cliente = ?", id_cliente)
        self.conexion.commit()