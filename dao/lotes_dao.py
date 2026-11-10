class LotesDAO:
    """Acceso a lotes e inventario. Las operaciones que tocan dos tablas
    se confirman con un solo commit (transacción)."""

    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
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
        cursor.execute(
            "SET NOCOUNT ON; "
            "INSERT INTO lotes (id_productor, id_producto, fecha_recepcion, peso_kg, "
            "                   humedad, precio_compra_kg) "
            "VALUES (?, ?, ?, ?, ?, ?); "
            "SELECT SCOPE_IDENTITY();",
            id_productor, id_producto, fecha, peso, humedad, precio,
        )
        id_lote = int(cursor.fetchone()[0])
        cursor.execute(
            "INSERT INTO inventario (id_lote, existencia_kg, bodega) VALUES (?, ?, ?)",
            id_lote, peso, bodega,
        )
        self.conexion.commit()

    def actualizar(self, id_lote, id_productor, id_producto, fecha, peso, humedad,
                   precio, bodega):
        cursor = self.conexion.cursor()
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
        cursor.execute("DELETE FROM inventario WHERE id_lote = ?", id_lote)
        cursor.execute("DELETE FROM lotes WHERE id_lote = ?", id_lote)
        self.conexion.commit()