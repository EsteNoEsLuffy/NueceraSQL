use nuecera
go

/* 1.- cuando se vende algo, descuenta los kilos del inventario
   (se ejecuta solo despues de cada insert en detalleventa) */
create or alter trigger trg_descuenta_inventario
on detalleventa
after insert
as
begin
/* "inserted" es una tabla temporal con las filas que se acaban de insertar */
update inventario
set existencia_kg = existencia_kg - i.cantidad_kg
from inventario inv inner join inserted i
on inv.id_lote = i.id_lote
end
go

/* 2.- cuando se actualiza o borra un lote, lo guarda en la bitacora
   "inserted" trae los valores nuevos y "deleted" los viejos */
create or alter trigger trg_bitacora_lotes
on lotes
after update, delete
as
begin
/* update: hay filas en inserted y en deleted, asi se puede mostrar
   el valor de antes y el de despues (viejo -> nuevo) */
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'lotes', 'update', i.id_lote,
concat('peso ', d.peso_kg, ' -> ', i.peso_kg,
', humedad ', d.humedad, ' -> ', i.humedad,
', precio compra ', d.precio_compra_kg, ' -> ', i.precio_compra_kg)
from inserted i inner join deleted d
on i.id_lote = d.id_lote

/* delete: solo hay filas en deleted (inserted esta vacia) */
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'lotes', 'delete', d.id_lote,
concat('se borro lote del productor ', d.id_productor, ' con peso ', d.peso_kg)
from deleted d
where not exists (select * from inserted)
end
go





/* 3.- cuando se registra una venta, deja un renglon en la bitacora por cada
   renglon del detalle. Se pone en detalleventa y no en ventas porque el total
   de ventas se calcula hasta el final (al insertar vale 0), y aqui ya vienen
   lote, kilos y subtotal. id_registro es el id de la venta. */
create or alter trigger trg_bitacora_ventas
on detalleventa
after insert
as
begin
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'ventas', 'insert', i.id_venta,
concat('lote ', i.id_lote, ', ', i.cantidad_kg, ' kg a ', i.precio_kg, '/kg, subtotal ', i.subtotal)
from inserted i
end
go


/* 4.- productores: registra altas, cambios y bajas.
   Un solo trigger para los 3 casos: si solo hay filas en inserted es alta,
   si solo hay en deleted es baja, y si hay en las dos es cambio */
create or alter trigger trg_bitacora_productores
on productores
after insert, update, delete
as
begin
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'productores', 'insert', i.id_productor,
concat('nuevo productor ', i.nombre, ', huerta ', i.huerta, ', tel ', i.telefono, ', ubicacion ', i.ubicacion)
from inserted i
where not exists (select * from deleted)

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'productores', 'update', i.id_productor,
concat('nombre ', d.nombre, ' -> ', i.nombre,
', telefono ', d.telefono, ' -> ', i.telefono,
', huerta ', d.huerta, ' -> ', i.huerta,
', ubicacion ', d.ubicacion, ' -> ', i.ubicacion)
from inserted i inner join deleted d
on i.id_productor = d.id_productor

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'productores', 'delete', d.id_productor,
concat('se borro productor ', d.nombre, ', huerta ', d.huerta)
from deleted d
where not exists (select * from inserted)
end
go

/* 5.- clientes: altas, cambios y bajas */
create or alter trigger trg_bitacora_clientes
on clientes
after insert, update, delete
as
begin
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'clientes', 'insert', i.id_cliente,
concat('nuevo cliente ', i.nombre, ', tel ', i.telefono, ', correo ', i.correo, ', direccion ', i.direccion)
from inserted i
where not exists (select * from deleted)

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'clientes', 'update', i.id_cliente,
concat('nombre ', d.nombre, ' -> ', i.nombre,
', telefono ', d.telefono, ' -> ', i.telefono,
', correo ', d.correo, ' -> ', i.correo,
', direccion ', d.direccion, ' -> ', i.direccion)
from inserted i inner join deleted d
on i.id_cliente = d.id_cliente

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'clientes', 'delete', d.id_cliente,
concat('se borro cliente ', d.nombre)
from deleted d
where not exists (select * from inserted)
end
go

/* 6.- productos: altas, cambios y bajas */
create or alter trigger trg_bitacora_productos
on productos
after insert, update, delete
as
begin
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'productos', 'insert', i.id_producto,
concat('nuevo producto ', i.nombre, ', precio ', i.precio_kg, '/kg')
from inserted i
where not exists (select * from deleted)

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'productos', 'update', i.id_producto,
concat('nombre ', d.nombre, ' -> ', i.nombre,
', precio ', d.precio_kg, ' -> ', i.precio_kg)
from inserted i inner join deleted d
on i.id_producto = d.id_producto

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'productos', 'delete', d.id_producto,
concat('se borro producto ', d.nombre)
from deleted d
where not exists (select * from inserted)
end
go

/* 7.- lotes: el trigger 2 solo cubria update y delete, aqui falta el insert
   (cuando llega un lote nuevo) */
create or alter trigger trg_bitacora_lotes_insert
on lotes
after insert
as
begin
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'lotes', 'insert', i.id_lote,
concat('nuevo lote del productor ', i.id_productor, ', producto ', i.id_producto,
', peso ', i.peso_kg, ' kg, humedad ', i.humedad, ', precio compra ', i.precio_compra_kg)
from inserted i
end
go

/* 8.- inventario: alta de existencia y cambio de bodega o ajuste manual.
   Las bajas por venta ya quedan en la bitacora de ventas, por eso el update
   solo registra cuando cambia la bodega */
create or alter trigger trg_bitacora_inventario
on inventario
after insert, update, delete
as
begin
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'inventario', 'insert', i.id_inventario,
concat('inventario del lote ', i.id_lote, ': ', i.existencia_kg, ' kg en bodega ', i.bodega)
from inserted i
where not exists (select * from deleted)

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'inventario', 'update', i.id_inventario,
concat('lote ', i.id_lote, ', existencia ', d.existencia_kg, ' -> ', i.existencia_kg,
', bodega ', d.bodega, ' -> ', i.bodega)
from inserted i inner join deleted d
on i.id_inventario = d.id_inventario
where isnull(d.bodega, '') <> isnull(i.bodega, '')

insert into bitacora (tabla, operacion, id_registro, detalle)
select 'inventario', 'delete', d.id_inventario,
concat('se borro inventario del lote ', d.id_lote)
from deleted d
where not exists (select * from inserted)
end
go
