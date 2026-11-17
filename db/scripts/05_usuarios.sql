/* usuarios de SQL Server para la app. Los permisos se manejan aqui y no en
   Python: la app entra con el usuario que se escribe en el login, y si ese
   usuario no tiene permiso, SQL Server lo rechaza. */
use master
go

/* el login es la cuenta a nivel servidor (con la que se inicia sesion) */
create login admin_Nancy with password = 'AdminNancy', check_policy = off, default_database = nuecera
create login ULimitado_Javi with password = 'LimitJavi', check_policy = off, default_database = nuecera
go

use nuecera
go

/* el user es ese mismo login pero dentro de la base nuecera */
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
inserta con los permisos de su dueno, y el deny insert no lo pararia
(si lo dejaramos, el usuario limitado podria vender aunque no pueda insertar) */
deny execute on sp_registrar_venta to ULimitado_Javi

/* la bitacora solo se lee, la llenan los triggers */
deny update on bitacora to ULimitado_Javi
go
