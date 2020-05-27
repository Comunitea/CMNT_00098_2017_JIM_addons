# -*- coding: utf-8 -*-

import models
import base
import controllers
from odoo import api

def post_init_actions(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})

	# SET WEBSITE PUBLISHED
	print(':: [SET WEBSITE PUBLISHED] Starts!')
	
	# All products
	products = env['product.template'].search([('type', 'like', 'product'), ('tag_ids', '!=', False), ('sale_ok', '=', True)])

	# Log info
	product_number = 0.0
	total_products = len(products)

	# For each product
	for product in products:

		product_number += 1
		percent = round((product_number / total_products) * 100, 2)
		print(":: %s%% PROCESANDO... [%s] %s" % (percent, product.default_code, product.name))
		product.website_published = True

		for variant in product.product_variant_ids:
			if variant.default_code and variant.attribute_names and variant.force_web != 'no':
				variant.website_published = True
			else:
				variant.website_published = False

	print(':: [SET WEBSITE PUBLISHED] Ends!')

	return True