class VentasDAO:
    """Consulta de ventas, registro y anulación mediante procedimientos almacenados."""

    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
        cursor.execute(
            "SELECT v.id_venta, v.fecha, c.nombre, pr.nombre, d.id_lote, "
            "       d.cantidad_kg, d.precio_kg, d.subtotal, v.total, v.usuario_bd "
            "FROM ventas v "
            "INNER JOIN clientes c ON v.id_cliente = c.id_cliente "
            "INNER JOIN detalleventa d ON v.id_venta = d.id_venta "
            "INNER JOIN lotes l ON d.id_lote = l.id_lote "
            "INNER JOIN productos pr ON l.id_producto = pr.id_producto "
            "ORDER BY v.fecha DESC, v.id_venta DESC"
        )
        return cursor.fetchall()

    def clientes(self):
        cursor = self.conexion.cursor()
        cursor.execute("SELECT id_cliente, nombre FROM clientes ORDER BY nombre")
        return cursor.fetchall()

    def lotes_disponibles(self):
        """Lotes con existencia, con su precio de lista para sugerirlo."""
        cursor = self.conexion.cursor()
        cursor.execute(
            "SELECT l.id_lote, pr.nombre, i.existencia_kg, pr.precio_kg "
            "FROM lotes l "
            "INNER JOIN inventario i ON i.id_lote = l.id_lote "
            "INNER JOIN productos pr ON l.id_producto = pr.id_producto "
            "WHERE i.existencia_kg > 0 "
            "ORDER BY l.id_lote"
        )
        return cursor.fetchall()

    def registrar(self, id_cliente, id_lote, cantidad, precio):
        cursor = self.conexion.cursor()
        cursor.execute("{CALL sp_registrar_venta (?, ?, ?, ?)}",
                       id_cliente, id_lote, cantidad, precio)
        id_venta = int(cursor.fetchone()[0])
        self.conexion.commit()
        return id_venta

    def anular(self, id_venta):
        cursor = self.conexion.cursor()
        cursor.execute("{CALL sp_anular_venta (?)}", id_venta)
        self.conexion.commit()