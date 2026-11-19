use nuecera
go

/* Carga a la bitacora lo que ya existia antes de crear los triggers
   (los triggers solo registran lo que pasa de ahi en adelante).
   Se puede ejecutar varias veces: el "not exists" evita duplicar renglones.
   Los renglones quedan con usuario 'carga_inicial'. */

/* productores */
insert into bitacora (tabla, operacion, id_registro, usuario, fecha, detalle)
select 'productores', 'insert', p.id_productor, 'carga_inicial', getdate(),
concat('nuevo productor ', p.nombre, ', huerta ', p.huerta, ', tel ', p.telefono, ', ubicacion ', p.ubicacion)
from productores p
where not exists (select * from bitacora b
where b.tabla = 'productores' and b.operacion = 'insert' and b.id_registro = p.id_productor)

/* clientes */
insert into bitacora (tabla, operacion, id_registro, usuario, fecha, detalle)
select 'clientes', 'insert', c.id_cliente, 'carga_inicial', getdate(),
concat('nuevo cliente ', c.nombre, ', tel ', c.telefono, ', correo ', c.correo, ', direccion ', c.direccion)
from clientes c
where not exists (select * from bitacora b
where b.tabla = 'clientes' and b.operacion = 'insert' and b.id_registro = c.id_cliente)

/* productos */
insert into bitacora (tabla, operacion, id_registro, usuario, fecha, detalle)
select 'productos', 'insert', p.id_producto, 'carga_inicial', getdate(),
concat('nuevo producto ', p.nombre, ', precio ', p.precio_kg, '/kg')
from productos p
where not exists (select * from bitacora b
where b.tabla = 'productos' and b.operacion = 'insert' and b.id_registro = p.id_producto)

/* lotes (usa la fecha de recepcion como fecha del registro) */
insert into bitacora (tabla, operacion, id_registro, usuario, fecha, detalle)
select 'lotes', 'insert', l.id_lote, 'carga_inicial', l.fecha_recepcion,
concat('nuevo lote del productor ', l.id_productor, ', producto ', l.id_producto,
', peso ', l.peso_kg, ' kg, humedad ', l.humedad, ', precio compra ', l.precio_compra_kg)
from lotes l
where not exists (select * from bitacora b
where b.tabla = 'lotes' and b.operacion = 'insert' and b.id_registro = l.id_lote)

/* inventario */
insert into bitacora (tabla, operacion, id_registro, usuario, fecha, detalle)
select 'inventario', 'insert', i.id_inventario, 'carga_inicial', getdate(),
concat('inventario del lote ', i.id_lote, ': ', i.existencia_kg, ' kg en bodega ', i.bodega)
from inventario i
where not exists (select * from bitacora b
where b.tabla = 'inventario' and b.operacion = 'insert' and b.id_registro = i.id_inventario)

/* ventas: un renglon por cada renglon del detalle, con la fecha y el usuario de la venta.
   Solo las ventas que todavia no tienen su renglon 'insert' en la bitacora */
insert into bitacora (tabla, operacion, id_registro, usuario, fecha, detalle)
select 'ventas', 'insert', d.id_venta, isnull(v.usuario_bd, 'carga_inicial'), v.fecha,
concat('lote ', d.id_lote, ', ', d.cantidad_kg, ' kg a ', d.precio_kg, '/kg, subtotal ', d.subtotal)
from detalleventa d inner join ventas v on v.id_venta = d.id_venta
where not exists (select * from bitacora b
where b.tabla = 'ventas' and b.operacion = 'insert' and b.id_registro = d.id_venta)
go

select * from bitacora order by id_bitacora desc
