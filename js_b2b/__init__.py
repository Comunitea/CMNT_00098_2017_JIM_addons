# -*- coding: utf-8 -*-

import models
import base
import controllers
from odoo import api, SUPERUSER_ID

def post_init_actions(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})

	# TODO: Mejorar esto, no se puede hacer con una consulta tan sencilla porque hay que comprobar que las compañías activadas tengan tarifa
	# -------------- SET VIP WEB ACCESS ON PARTNERS --------------

	print(':: [SET VIP WEB ACCESS] Starts!')

	""" Copiar valores de res_partner_res_company_rel a res_partner_res_company_web_access
	omitiendo las empresas en las que el cliente no tiene tarifa """
	cr.execute("INSERT INTO res_partner_res_company_web_access \
					(SELECT res_partner_id, res_company_id FROM res_company_res_partner_rel \
					LEFT JOIN ir_property ON ir_property.res_id = 'res.partner,' || res_partner_id AND ir_property.company_id = res_company_id AND name LIKE 'property_product_pricelist' \
					WHERE ir_property.id IS NOT NULL \
					GROUP BY res_partner_id, res_company_id)")

	print(':: [SET VIP WEB ACCESS] Ends!')

	# -------------- SET WEBSITE PUBLISHED ON PRODUCTS --------------

	print(':: [SET WEBSITE PUBLISHED] Starts!')

	# Default Web Category
	default_public_cat = env.ref('js_b2b.web_category_1')
	
	# All published products but not with tag 50 (J0008-IMPORTACIÓN)
	product_ids = env['product.template'].with_context(active_test=False)\
	.search([('type', 'like', 'product'), ('tag_ids', '!=', False), ('sale_ok', '=', True)])\
	.filtered(lambda p: 50 not in p.tag_ids.ids).ids

	# Log info
	product_number = 0.0
	total_products = len(product_ids)
	total_variants = 0

	# For each product
	for product_id in product_ids:
		product = env['product.template'].browse(product_id)
		product_number += 1
		percent = round((product_number / total_products) * 100, 2)
		print(":: %s%% PROCESANDO... [%s] %s" % (percent, product.default_code, product.name))

		print("- ESTABLECIENDO CATEGORIA WEB POR DEFECTO DEL PRODUCTO %s" % product.default_code, default_public_cat.name)

		# Set default web category on published products
		product.public_categ_ids = [default_public_cat.id,]

		# Set website published
		try:
			print("- PUBLICANDO PRODUCTO %s" % product.default_code)
			product.with_context(b2b_evaluate=False).write({ 'website_published': True })
		except Exception as e:
			print("- ERROR: %s" % e)
		else:
			total_products += 1

		# Set variant website published
		for variant in product.product_variant_ids:
			if variant.default_code and variant.attribute_names and variant.force_web != 'no':
				try:
					print("- PUBLICANDO VARIANTE %s" % variant.default_code)
					variant.with_context(b2b_evaluate=False).write({ 'website_published': True })
				except Exception as e:
					print("- ERROR: %s" % e)
				else:
					total_variants += 1
			else:
				variant.with_context(b2b_evaluate=False).write({ 'website_published': False })

	print(':: PRODUCTS PUBLISHED', total_products)
	print(':: VARIANTS PUBLISHED', total_variants)
	print(':: [SET WEBSITE PUBLISHED] Ends!')

	return True