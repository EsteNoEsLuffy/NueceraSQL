create database nuecera
use nuecera

create table productores (
id_productor int primary key identity (1,1),
nombre nvarchar (50),
telefono nvarchar (20),
huerta nvarchar (100),
ubicacion nvarchar (150)
)

create table clientes (
id_cliente int primary key identity (1,1),
nombre nvarchar (100),
telefono nvarchar (20),
correo nvarchar (120),
direccion nvarchar (150)
)

create table productos (
id_producto int primary key identity (1,1),
nombre nvarchar (80),
precio_kg decimal (10,2)
)

create table lotes (
id_lote int primary key identity (1,1),
id_productor int references productores (id_productor),
id_producto int references productos (id_producto),
fecha_recepcion date default getdate(),
peso_kg decimal (10,2),
humedad decimal (5,2),
precio_compra_kg decimal (10,2)
)

/* un lote tiene un solo renglon de inventario (por eso unique) */
create table inventario (
id_inventario int primary key identity (1,1),
id_lote int unique references lotes (id_lote),
existencia_kg decimal (10,2) check (existencia_kg >= 0),
bodega nvarchar (50)
)

create table ventas (
id_venta int primary key identity (1,1),
id_cliente int references clientes (id_cliente),
fecha datetime default getdate(),
total decimal (12,2) default 0,
usuario_bd nvarchar (128) default suser_sname()
)

create table detalleventa (
id_detalle int primary key identity (1,1),
id_venta int references ventas (id_venta),
id_lote int references lotes (id_lote),
cantidad_kg decimal (10,2),
precio_kg decimal (10,2),
subtotal decimal (12,2)
)

create table bitacora (
id_bitacora int primary key identity (1,1),
tabla nvarchar (50),
operacion nvarchar (10),
id_registro int,
usuario nvarchar (128) default suser_sname(),
fecha datetime default getdate(),
detalle nvarchar (500)
)


select* from bitacora