/*
SELECT
    tc.constraint_name, tc.table_name, kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY' AND ccu.table_name='product_uom'
order by kcu.column_name;
*/
CREATE OR REPLACE FUNCTION replace_uom(old_id INT, new_id INT)
    RETURNS void AS $$
    BEGIN
	update account_invoice_line set uom_id = $2 where uom_id = $1;
	update sale_order_line set product_uom = $2 where product_uom =$1;
	update sale_order_line_template set product_uom = $2 where product_uom =$1;
	update stock_move set product_uom = $2 where product_uom =$1;
	update procurement_order set product_uom = $2 where product_uom =$1;
	update purchase_order_line set product_uom = $2 where product_uom =$1;
	update mrp_product_produce set product_uom_id = $2 where product_uom_id =$1;
	update mrp_unbuild set product_uom_id = $2 where product_uom_id =$1;
	update account_analytic_line set product_uom_id = $2 where product_uom_id =$1;
	update account_move_line set product_uom_id = $2 where product_uom_id =$1;
	update mrp_bom_line set product_uom_id = $2 where product_uom_id =$1;
	update mrp_bom set product_uom_id = $2 where product_uom_id =$1;
	update mrp_production set product_uom_id = $2 where product_uom_id =$1;
	update stock_inventory_line set product_uom_id = $2 where product_uom_id =$1;
	update stock_pack_operation set product_uom_id = $2 where product_uom_id =$1;
	update stock_production_lot set product_uom_id = $2 where product_uom_id =$1;
	update stock_scrap set product_uom_id = $2 where product_uom_id =$1;
	update res_company set project_time_mode_id = $2 where project_time_mode_id =$1;
	update account_invoice_line set uom_id = $2 where uom_id =$1;
	update make_procurement set uom_id = $2 where uom_id =$1;
	update product_template set uom_id = $2 where uom_id =$1;
	update product_template set uom_po_id = $2 where uom_po_id =$1;
	update stock_move set weight_uom_id = $2 where weight_uom_id =$1;
	update stock_picking set weight_uom_id = $2 where weight_uom_id =$1;
	
    END;
    $$ LANGUAGE plpgsql;


/* replace (old_id, new_id) */
select replace_uom(30,1)


