# -*- coding: utf-8 -*-

import models
import base
import controllers
from odoo import api

def __partner_actions(env):
	print(':: [SET VIP WEB ACCESS] Starts!')

	partner_ids = env['res.partner'].with_context(active_test=False).search([('group_companies_ids', '!=', False)])._ids

	# Log info
	partner_number = 0.0
	total_partners = len(partner_ids)
	excluded_partners = list()

	# For each partner
	for partner_id in partner_ids:
		partner = self.env['res.partner'].browse(partner_id)
		# jim_sale Comunitea limitation (only Spain partners with state or for other countries)
		if (partner.country_id and partner.country_id.id == 69 and partner.state_id) or (partner.country_id and partner.country_id.id != 69) or not partner.country_id:
			partner_number += 1
			percent = round((partner_number / total_partners) * 100, 2)
			print(":: %s%% PROCESANDO... [%s] %s" % (percent, partner.ref, partner.name))
			partner.vip_web_access = partner.group_companies_ids
		else:
			excluded_partners.append(partner.name)

	partner_excluded_num = len(excluded_partners)
	print(':: TOTAL PARTNERS', total_partners)
	print(':: PARTNERS PROCESSED', total_partners - partner_excluded_num)
	print(':: PARTNERS EXCLUDED', partner_excluded_num)
	print(':: EXCLUDED LIST', excluded_partners)
	print(':: [SET VIP WEB ACCESS] Ends!')

def __product_actions(env):
	print(':: [SET WEBSITE PUBLISHED] Starts!')
	
	# All products
	product_ids = env['product.template'].with_context(active_test=False).search([('type', 'like', 'product'), ('tag_ids', '!=', False), ('sale_ok', '=', True)])._ids

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

		# Set default web category on published products
		product.public_categ_ids = (6, 0, [env.ref('js_b2b.web_category_1').id])
		
		# Set website published
		product.website_published = True

		# Set variant website published
		for variant in product.product_variant_ids:
			if variant.default_code and variant.attribute_names and variant.force_web != 'no':
				variant.website_published = True
				total_variants += 1
			else:
				variant.website_published = False

	print(':: PRODUCTS PUBLISHED', total_products)
	print(':: VARIANTS PUBLISHED', total_variants)
	print(':: [SET WEBSITE PUBLISHED] Ends!')

def post_init_actions(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})

	# -------------- SET VIP WEB ACCESS ON PARTNERS --------------
	__partner_actions(env)

	# -------------- SET WEBSITE PUBLISHED ON PRODUCTS --------------
	__product_actions(env)

	return True