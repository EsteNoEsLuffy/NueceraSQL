# DAO = la capa que habla con la base de datos. Aqui va todo el SQL de la tabla
# clientes, asi las pantallas no tienen que saber nada de consultas.
class ClientesDAO:
    def __init__(self, conexion):
        # la conexion es la del usuario que inicio sesion, entonces SQL Server
        # le aplica sus permisos a cada consulta
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
        # los ? se llenan con los parametros de abajo; asi no se arma el SQL
        # pegando texto y evitamos la inyeccion SQL
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, correo, direccion) "
            "VALUES (?, ?, ?, ?)",
            nombre, telefono, correo, direccion,
        )
        # sin commit los cambios no se guardan en la base
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
        # si el cliente ya tiene ventas, SQL Server rechaza el DELETE por la
        # llave foranea y la pantalla muestra el error
        cursor.execute("DELETE FROM clientes WHERE id_cliente = ?", id_cliente)
        self.conexion.commit()
