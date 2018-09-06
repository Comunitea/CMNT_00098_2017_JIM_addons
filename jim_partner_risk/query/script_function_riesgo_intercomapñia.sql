drop function if exists updatepropertyrisklimit;

CREATE OR REPLACE FUNCTION updatepropertyrisklimit(integer[], boolean, integer)
RETURNS void
AS $$
declare 
company_ids  INT[];
company_id record;
field record;
force_value boolean;
forced integer;
BEGIN
company_ids = $1;
force_value = $2;
forced = $3;

delete from ir_property ip where ip.fields_id in (select id from ir_model_fields where ttype='boolean' and model_id = 79 and name ilike 'risk%include') and ip.company_id = ANY(company_ids);

FOR company_id IN SELECT id FROM res_company where id = ANY(company_ids)
    LOOP
	for field in 
	(select id as field_id, name as field_name, model as model, model_id as model_id from ir_model_fields where ttype='boolean' and model_id = 79 and name ilike 'risk%include')
	
	loop 		
		/* 
			delete from ir_property ip where ip.fields_id = field.field_id and ip.company_id = company_id.id;
		*/
		
		insert into 
		ir_property
		("create_date", "write_date", "create_uid", "write_uid", "value_integer", "name", "res_id", "company_id", "fields_id", "type")
		(select now(), now(), 1, 1,
		
		case 
			when not force_value and field.field_name ='risk_invoice_open_include' then COALESCE(risk_invoice_open_include, false)::bool::int
			when not force_value and field.field_name ='risk_account_amount_unpaid_include' then COALESCE(risk_account_amount_unpaid_include, false)::bool::int
			when not force_value and field.field_name ='risk_invoice_draft_include' then COALESCE(risk_invoice_draft_include, false)::bool::int
			when not force_value and field.field_name ='risk_invoice_unpaid_include' then COALESCE(risk_invoice_unpaid_include, false)::bool::int 
			when not force_value and field.field_name ='risk_account_amount_include' then COALESCE(risk_account_amount_include, false)::bool::int
			when not force_value and field.field_name ='risk_sale_order_include' then COALESCE(risk_sale_order_include, false)::bool::int
			when force_value then forced
		end,	
		field.field_name,
		field.model || ',' || id,
		company_id.id,
		field.field_id,
		'boolean'
		from res_partner rp where customer = true);
	end loop; 
    END LOOP;


RETURN;
END;
$$ LANGUAGE plpgsql;

/* COMPAÑIA 1 SIN FORZAR*/
select updatepropertyrisklimit('{1}'::int[], false, 0);
/* COMPAÑIA 5,8 FORZAR A 1*/
select updatepropertyrisklimit('{5,8}'::int[], true, 1);
/* resto compañias > FORZAR A 0*/
select updatepropertyrisklimit('{4,6,7,12,13,16,9,17,18}'::int[], true, 0);

