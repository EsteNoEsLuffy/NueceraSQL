class InventarioDAO:
    """Consulta de inventario y cambio de bodega."""

    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
        cursor.execute(
            "SELECT i.id_lote, pr.nombre, p.nombre, i.existencia_kg, i.bodega "
            "FROM inventario i "
            "INNER JOIN lotes l ON i.id_lote = l.id_lote "
            "INNER JOIN productos pr ON l.id_producto = pr.id_producto "
            "INNER JOIN productores p ON l.id_productor = p.id_productor "
            "ORDER BY i.id_lote"
        )
        return cursor.fetchall()

    def cambiar_bodega(self, id_lote, bodega):
        cursor = self.conexion.cursor()
        cursor.execute(
            "UPDATE inventario SET bodega = ? WHERE id_lote = ?", bodega, id_lote
        )
        self.conexion.commit()