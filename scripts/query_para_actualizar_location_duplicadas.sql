/*Quants en ubicaciones no activas*/
select sl2.name, sl.name, * from stock_quant sq
join stock_location sl on sl.id = sq.location_id
join stock_location sl2 on sl2.id = sl.location_id
where sq.location_id in (select id from stock_location where not active) 
/*Ubicaciones de exsitencias duplicadas de EME y TRI*/
select sl1.id, sl1.name, sl1.active, sl2.id as parent_id, sl2.name as parent_name, sl2.active as parent_active from stock_location sl1 
join stock_location sl2 on sl2.id = sl1.location_id
where sl2.name in ('TRI', 'MEL') and sl1.name = 'Existencias'

/* Para MEL/Existencias*/
update stock_quant set location_id = 67 where location_id = 124
update stock_move where location_id = 67 where location_id = 124
update stock_move where location_dest_id = 67 where location_dest_id = 124
update stock_picking where location_id = 67 where location_id = 124
update stock_picking where location_dest_id = 67 where location_dest_id = 124

/* Para TRI/Existencias*/
update stock_quant set location_id = 236 where location_id = 247


