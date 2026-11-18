/*
  Base de datos de la nuecera: compramos nuez a productores, la guardamos en
  bodegas y se la vendemos a clientes.

  Como se relacionan las tablas:
    productores --< lotes >-- productos
                      |
                      +-- 1:1 -- inventario
                      |
    clientes --< ventas --< detalleventa >-- lotes
    bitacora (historial de cambios, la llenan los triggers)
  ( --< significa "uno a muchos" )
*/
create database nuecera
use nuecera

/* los que nos venden la nuez. Un productor puede entregar muchos lotes */
create table productores (
id_productor int primary key identity (1,1), /* identity: SQL Server pone el numero solo, empieza en 1 y sube de 1 en 1 */
nombre nvarchar (50),
telefono nvarchar (20),   /* es texto porque puede llevar lada, guiones, etc. */
huerta nvarchar (100),    /* nombre de su huerta */
ubicacion nvarchar (150)
)

/* a quienes les vendemos */
create table clientes (
id_cliente int primary key identity (1,1),
nombre nvarchar (100),
telefono nvarchar (20),
correo nvarchar (120),
direccion nvarchar (150)
)

/* catalogo de productos que manejamos (mitades, entera, con cascara) */
create table productos (
id_producto int primary key identity (1,1),
nombre nvarchar (80),
precio_kg decimal (10,2)  /* precio de lista de venta; en la venta se puede cambiar */
)

/* cada entrega de nuez que recibimos de un productor */
create table lotes (
id_lote int primary key identity (1,1),
id_productor int references productores (id_productor), /* llave foranea: no deja poner un productor que no existe */
id_producto int references productos (id_producto),
fecha_recepcion date default getdate(),  /* si no se manda fecha, usa la de hoy */
peso_kg decimal (10,2),                  /* kilos que llegaron */
humedad decimal (5,2),                   /* porcentaje de humedad al recibirla */
precio_compra_kg decimal (10,2)          /* lo que le pagamos al productor por kilo */
)

/* un lote tiene un solo renglon de inventario (por eso unique) */
/* aqui se guardan los kilos que le quedan a cada lote: baja con las ventas */
create table inventario (
id_inventario int primary key identity (1,1),
id_lote int unique references lotes (id_lote),
existencia_kg decimal (10,2) check (existencia_kg >= 0), /* el check evita que quede en negativo */
bodega nvarchar (50)
)

/* encabezado de la venta: quien compro, cuando y cuanto fue en total */
create table ventas (
id_venta int primary key identity (1,1),
id_cliente int references clientes (id_cliente),
fecha datetime default getdate(),
total decimal (12,2) default 0,                 /* se calcula al final sumando el detalle */
usuario_bd nvarchar (128) default suser_sname() /* quien hizo la venta: el usuario de SQL Server con el que entro a la app */
)

/* renglones de la venta: de que lote salio la nuez, cuantos kilos y a que precio */
create table detalleventa (
id_detalle int primary key identity (1,1),
id_venta int references ventas (id_venta),
id_lote int references lotes (id_lote),
cantidad_kg decimal (10,2),
precio_kg decimal (10,2),
subtotal decimal (12,2)   /* cantidad_kg * precio_kg */
)

/* historial de cambios importantes (modificar o borrar lotes, anular ventas).
   Nadie la puede llena a mano (usuarios): lo hacen los triggers y el procedimiento almacenado de anular */
create table bitacora (
id_bitacora int primary key identity (1,1),
tabla nvarchar (50),     /* en que tabla paso */
operacion nvarchar (10), /* update o delete */
id_registro int,         /* id del registro afectado */
usuario nvarchar (128) default suser_sname(),
fecha datetime default getdate(),
detalle nvarchar (500)   /* texto con lo que cambio */
)


select* from bitacora
