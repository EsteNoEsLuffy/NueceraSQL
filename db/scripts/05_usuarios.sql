use master
go

create login admin_Nancy with password = 'AdminNancy', check_policy = off, default_database = nuecera
create login ULimitado_Javi with password = 'LimitJavi', check_policy = off, default_database = nuecera
go

use nuecera
go

create user admin_Nancy for login admin_Nancy
create user ULimitado_Javi for login ULimitado_Javi
go

/* admin: todos los permisos */
alter role db_owner add member admin_Nancy

/* limitado: solo consulta y actualiza */
grant select, update on schema::dbo to ULimitado_Javi

/* puede sacar el reporte */
grant execute on sp_ventas_por_fecha to ULimitado_Javi

/* no puede insertar ni eliminar */
deny insert, delete on schema::dbo to ULimitado_Javi

/* a sp_registrar_venta se le niega el execute porque el procedimiento
inserta con los permisos de su due�o, y el deny insert no lo pararia */
deny execute on sp_registrar_venta to ULimitado_Javi

/* la bitacora solo se lee, la llenan los triggers */
deny update on bitacora to ULimitado_Javi
go


