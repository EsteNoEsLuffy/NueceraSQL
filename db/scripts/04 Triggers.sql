use nuecera
go

/* 1.- cuando se vende algo, descuenta los kilos del inventario */
create or alter trigger trg_descuenta_inventario
on detalleventa
after insert
as
begin
update inventario
set existencia_kg = existencia_kg - i.cantidad_kg
from inventario inv inner join inserted i
on inv.id_lote = i.id_lote
end
go

/* 2.- cuando se actualiza o borra un lote, lo guarda en la bitacora */
create or alter trigger trg_bitacora_lotes
on lotes
after update, delete
as
begin
/* update: hay filas en inserted y en deleted */
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'lotes', 'update', i.id_lote,
concat('peso ', d.peso_kg, ' -> ', i.peso_kg,
', humedad ', d.humedad, ' -> ', i.humedad,
', precio compra ', d.precio_compra_kg, ' -> ', i.precio_compra_kg)
from inserted i inner join deleted d
on i.id_lote = d.id_lote

/* delete: solo hay filas en deleted */
insert into bitacora (tabla, operacion, id_registro, detalle)
select 'lotes', 'delete', d.id_lote,
concat('se borro lote del productor ', d.id_productor, ' con peso ', d.peso_kg)
from deleted d
where not exists (select * from inserted)
end
go

