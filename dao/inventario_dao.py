# El inventario no se crea ni se borra desde aqui: su renglon nace junto con el
# lote (ver lotes_dao) y baja o sube con las ventas. Lo unico que se puede
# cambiar a mano es la bodega.
class InventarioDAO:
    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
        # inventario solo tiene el id del lote, asi que unimos con lotes para
        # llegar al producto y al productor y mostrar sus nombres
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
