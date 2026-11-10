use nuecera

insert into productores values ('juan perez ramirez','6141234567','huerta la esperanza','delicias, chihuahua')
insert into productores values ('maria lopez soto','6269876543','huerta los alamos','camargo, chihuahua')
insert into productores values ('roberto garcia mena','6391112233','huerta el pecanal','jimenez, chihuahua')

insert into clientes values ('dulces y botanas del norte','6144445566','compras@botanasnorte.com','av universidad 100'),
('abarrotes hernandez','6147778899','contacto@abarroteshdz.com','calle 20 #305'),
('exportadora pecan mx','6141230000','ventas@pecanmx.com','parque industrial')

insert into productos values ('nuez pecanera en mitades',320),
('nuez pecanera entera',280),
('nuez pecanera con cascara',150)

/* lotes: productor, producto, fecha, peso, humedad, precio de compra por kg */
insert into lotes values (1,3,'2026-10-05',1200,4.5,110),
(2,2,'2026-10-12',800,4,200),
(3,1,'2026-10-20',500,3.8,240),
(1,1,'2026-10-28',650,4.2,235)

/* inventario: lote, existencia, bodega */
insert into inventario values (1,1200,'bodega a'),
(2,800,'bodega a'),
(3,500,'bodega b'),
(4,650,'bodega b')

select * from productores
select * from lotes
select * from inventario