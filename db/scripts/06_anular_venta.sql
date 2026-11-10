use nuecera
go

create procedure sp_anular_venta
@id_venta int
as
begin
set nocount on

begin transaction anula
begin try
	if not exists (select 1 from ventas where id_venta = @id_venta)
		raiserror ('la venta no existe',16,1)

	declare @total decimal(12,2)
	select @total = total from ventas where id_venta = @id_venta

	/* devuelve los kilos al inventario */
	update inv
	set inv.existencia_kg = inv.existencia_kg + d.cantidad_kg
	from inventario inv
	inner join detalleventa d on inv.id_lote = d.id_lote
	where d.id_venta = @id_venta

	delete from detalleventa where id_venta = @id_venta
	delete from ventas where id_venta = @id_venta

	insert into bitacora (tabla, operacion, id_registro, detalle)
	values ('ventas', 'delete', @id_venta,
	concat('venta anulada, total ', @total, ', kilos devueltos al inventario'))

	commit tran anula
end try
begin catch
	rollback tran anula;
	throw
end catch
end
go

/* solo el admin puede anular (db_owner ya tiene permiso) */
deny execute on sp_anular_venta to ULimitado_Javi
go