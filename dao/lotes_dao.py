# Un lote es una entrega de nuez de un productor. Cada lote tiene un renglon
# en inventario con los kilos que quedan, por eso aqui casi todo toca dos tablas.
class LotesDAO:
    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
        # LEFT JOIN con inventario por si algun lote no tuviera su renglon;
        # asi igual aparece en la lista (con existencia vacia).
        # Al final van los dos ids, la pantalla los usa para editar
        cursor.execute(
            "SELECT l.id_lote, p.nombre, pr.nombre, l.fecha_recepcion, l.peso_kg, "
            "       l.humedad, l.precio_compra_kg, i.existencia_kg, i.bodega, "
            "       l.id_productor, l.id_producto "
            "FROM lotes l "
            "INNER JOIN productores p ON l.id_productor = p.id_productor "
            "INNER JOIN productos pr ON l.id_producto = pr.id_producto "
            "LEFT JOIN inventario i ON i.id_lote = l.id_lote "
            "ORDER BY l.fecha_recepcion DESC, l.id_lote DESC"
        )
        return cursor.fetchall()

    # estas dos llenan los desplegables del formulario
    def productores(self):
        cursor = self.conexion.cursor()
        cursor.execute("SELECT id_productor, nombre FROM productores ORDER BY nombre")
        return cursor.fetchall()

    def productos(self):
        cursor = self.conexion.cursor()
        cursor.execute("SELECT id_producto, nombre FROM productos ORDER BY nombre")
        return cursor.fetchall()

    def insertar(self, id_productor, id_producto, fecha, peso, humedad, precio, bodega):
        cursor = self.conexion.cursor()
        # SET NOCOUNT ON evita que SQL Server mande el conteo de filas afectadas,
        # que pyodbc confunde con un resultado; asi el fetchone trae el SELECT.
        # SCOPE_IDENTITY() devuelve el id que se acaba de generar para el lote
        cursor.execute(
            "SET NOCOUNT ON; "
            "INSERT INTO lotes (id_productor, id_producto, fecha_recepcion, peso_kg, "
            "                   humedad, precio_compra_kg) "
            "VALUES (?, ?, ?, ?, ?, ?); "
            "SELECT SCOPE_IDENTITY();",
            id_productor, id_producto, fecha, peso, humedad, precio,
        )
        id_lote = int(cursor.fetchone()[0])
        # al recibir el lote, la existencia inicial es todo su peso
        cursor.execute(
            "INSERT INTO inventario (id_lote, existencia_kg, bodega) VALUES (?, ?, ?)",
            id_lote, peso, bodega,
        )
        # un solo commit para las dos tablas: o se guardan ambas o ninguna
        self.conexion.commit()

    def actualizar(self, id_lote, id_productor, id_producto, fecha, peso, humedad,
                   precio, bodega):
        cursor = self.conexion.cursor()
        # ojo: aqui no se toca la existencia, solo la bodega. Si se corrige el
        # peso de un lote que ya tuvo ventas, la existencia no se recalcula
        cursor.execute(
            "UPDATE lotes SET id_productor = ?, id_producto = ?, fecha_recepcion = ?, "
            "peso_kg = ?, humedad = ?, precio_compra_kg = ? WHERE id_lote = ?",
            id_productor, id_producto, fecha, peso, humedad, precio, id_lote,
        )
        cursor.execute(
            "UPDATE inventario SET bodega = ? WHERE id_lote = ?", bodega, id_lote
        )
        self.conexion.commit()

    def eliminar(self, id_lote):
        cursor = self.conexion.cursor()
        # primero el inventario porque depende del lote (llave foranea).
        # Si el lote ya se vendio, el segundo DELETE falla y no se guarda nada
        cursor.execute("DELETE FROM inventario WHERE id_lote = ?", id_lote)
        cursor.execute("DELETE FROM lotes WHERE id_lote = ?", id_lote)
        self.conexion.commit()
