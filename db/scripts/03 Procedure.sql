use nuecera
go

/* 1.- registra una venta de un lote -------------------------------- procedure 1*/
create procedure sp_registrar_venta
@id_cliente int,
@id_lote int,
@cantidad_kg decimal (10,2),
@precio_kg decimal (10,2)
as
begin /*main*/
set nocount on
declare @existencia decimal (10,2)
declare @id_venta int

begin transaction venta
begin try
	select @existencia = existencia_kg
	from inventario
	where id_lote = @id_lote

	/* cada raiserror manda directo al catch */
	if @cantidad_kg <= 0
		raiserror ('la cantidad debe ser mayor a cero',16,1)

	if not exists (select 1 from clientes where id_cliente = @id_cliente)
		raiserror ('el cliente no existe',16,1)

	if @existencia is null
		raiserror ('el lote no existe en inventario',16,1)

	if @existencia < @cantidad_kg
		raiserror ('no hay suficiente existencia en el lote',16,1)

	insert into ventas (id_cliente) values (@id_cliente)
	set @id_venta = scope_identity()

	/* este insert dispara el trigger trg_descuenta_inventario */
	insert into detalleventa (id_venta, id_lote, cantidad_kg, precio_kg, subtotal)
	values (@id_venta, @id_lote, @cantidad_kg, @precio_kg, @cantidad_kg * @precio_kg)

	update ventas
	set total = (select sum(subtotal) from detalleventa where id_venta = @id_venta)
	where id_venta = @id_venta

	commit tran venta
	select @id_venta as id_venta
end try
begin catch
	rollback tran venta;
	/* throw vuelve a mandar el error para que la app lo reciba y lo muestre */
	throw
end catch
end /*fin del main*/
go

/* 2.- ventas entre dos fechas (el que usa el reporte pdf)-------------------------------- procedure 2 */
create procedure sp_ventas_por_fecha
@fecha_inicio date,
@fecha_fin date
as
begin
set nocount on

select v.id_venta, v.fecha, c.nombre as cliente, p.nombre as producto,
d.id_lote, d.cantidad_kg, d.precio_kg, d.subtotal, v.total as total_venta, v.usuario_bd
from ventas v
inner join clientes c on v.id_cliente = c.id_cliente
inner join detalleventa d on v.id_venta = d.id_venta
inner join lotes l on d.id_lote = l.id_lote
inner join productos p on l.id_producto = p.id_producto
where v.fecha >= @fecha_inicio and v.fecha < dateadd(day, 1, @fecha_fin)
order by v.fecha, v.id_venta
end
go

