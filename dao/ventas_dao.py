# Aqui las ventas no se insertan con INSERT directo: se hacen con procedimientos
# almacenados (sp_registrar_venta y sp_anular_venta) para que toda la logica
# (revisar existencia, descontar inventario, calcular total) viva en la base
# y salga bien sin importar desde donde se llame.
class VentasDAO:
    def __init__(self, conexion):
        self.conexion = conexion

    def listar(self):
        cursor = self.conexion.cursor()
        # una venta con su detalle: ventas -> cliente, y detalleventa -> lote -> producto
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
        # solo los lotes que todavia tienen nuez; el precio de lista del producto
        # se usa como precio sugerido en el formulario
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
        # el procedimiento termina con un SELECT del id de la venta nueva
        id_venta = int(cursor.fetchone()[0])
        self.conexion.commit()
        return id_venta

    def anular(self, id_venta):
        cursor = self.conexion.cursor()
        cursor.execute("{CALL sp_anular_venta (?)}", id_venta)
        self.conexion.commit()
