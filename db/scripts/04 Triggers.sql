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
