# -*- coding: utf-8 -*-
from odoo import api, fields, models
from ..base.helper import JSync
from datetime import datetime
import os

class B2BBulkExport(models.Model):
	_name = "b2b.export"

	_prices_precision = 2
	_log_filename = 'b2b.export.log'

	def write_to_log(self, txt):
		module_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
		log_file = os.path.join(module_dir, 'static', 'log', self._log_filename)
		with open(log_file, "aw+") as file:
			date = datetime.now()
			file.write("%s %s\n" % (date, txt))
			print("%s %s\n" % (date, txt))

	def test_recursion_pablolp(self, test='A', test_limit=2):
		# TEST A
		if test == 'A':
			start_time = datetime.now()
			print("TEST A: RECORDSET CON %s PRODUCTOS" % test_limit)
			products = self.env['product.product'].search([('website_published', '=', True)], limit=test_limit)
			for product in products:
				print(product.name, product.web_global_stock)
			time_elapsed = datetime.now() - start_time
			print("TEST A Finalizado en %s milisegundos" % (time_elapsed.microseconds/1000))

		# TEST B
		if test == 'B':
			start_time = datetime.now()
			products = self.env['product.product'].search([('website_published', '=', True)], limit=test_limit).ids
			print("TEST B: %s PRODUCTOS INDEPENDIENTES" % test_limit)
			for product_id in products:
				product = self.env['product.product'].browse(product_id)
				print(product.name, product.web_global_stock)
			time_elapsed = datetime.now() - start_time
			print("TEST B Finalizado en %s milisegundos" % (time_elapsed.microseconds/1000))

	def covert_published_products(self):
		self.write_to_log('[covert_published_products] Starts!')
		# All products
		products = self.env['product.template'].search([('type', 'like', 'product'), ('tag_ids', '!=', False), ('sale_ok', '=', True)])
		# Log info
		product_number = 0.0
		total_products = len(products)
		# For each product
		for product in products:
			product_number += 1
			percent = round((product_number / total_products) * 100, 2)
			self.write_to_log(":: %s%% PROCESANDO... [%s] %s" % (percent, product.default_code, product.name))
			product.website_published = True
			for variant in product.product_variant_ids:
				if variant.default_code and variant.attribute_names and variant.force_web != 'no':
					variant.website_published = True
				else:
					variant.website_published = False

		self.write_to_log('[covert_published_products] Ends!')

	def __pricelists_unique_quantities(self):
		unique_quantities = self.env['product.pricelist.item'].read_group([], ('min_quantity'), groupby=('min_quantity'), orderby=('min_quantity ASC'), lazy=True)
		unique_quantities = [qty['min_quantity'] for qty in unique_quantities]
		# Remove 0 from quantities if exists
		if 0 in unique_quantities:
			unique_quantities.remove(0)
		# Add 1 on quantities if not exists
		if 1 not in unique_quantities:
			unique_quantities.add(1)
		# Return sorted tuple
		return sorted(tuple(unique_quantities))

	def b2b_pricelists_prices(self, test_limit=None):
		self.write_to_log('[b2b_pricelists_prices] Starts!')
		# Out prices
		prices = list()
		# All pricelists
		pricelists = self.env['product.pricelist'].search([('active', '=', True)])
		# All products
		products_ids = self.env['product.template'].search([('website_published', '=', True)], limit=test_limit).ids
		# All quantities
		quantities = self.__pricelists_unique_quantities()
		# Log info
		total_pricelists = len(pricelists)
		total_products = len(products_ids)
		product_number = 0.0
		self.write_to_log('# LISTAS DE PRECIOS: %s' % total_pricelists)
		self.write_to_log('# PRODUCTOS: %s' % total_products)
		self.write_to_log('# CANTIDADES A CALCULAR: %s' % quantities)
		# For each pricelist
		for pricelist in pricelists:
			# For each product
			for product_id in products_ids:
				product_number += 1
				percent = round(((product_number / total_products) * 100) / total_pricelists, 2)
				# For each quantity
				for min_qty in quantities:
					# Product in pricelist & qty context
					product_in_ctx = self.env['product.template'].with_context({ 'pricelist': pricelist.name, 'quantity': min_qty }).browse(product_id)
					self.write_to_log(":: %s%% PROCESANDO... [%s] %s" % (percent, product_in_ctx.default_code, product_in_ctx.name))
					# Get all variant prices
					variants_prices = product_in_ctx.product_variant_ids.mapped('price')
					# Same price in all variants
					if all(x==variants_prices[0] for x in variants_prices if variants_prices[0]):
						price = round(product_in_ctx.product_variant_id.price, self._prices_precision)
						# If price is not 0 and not in prices list yet
						product_filter = filter(lambda x: x['pricelist_id'] == pricelist.id and x['product_id'] == product_id and x['variant_id'] == None and x['quantity'] == min_qty and x['price'] == price, prices)
						if price and not bool(list(product_filter)):
							prices.append({ 
								'pricelist_id': pricelist.id,
								'product_id': product_in_ctx.id,
								'variant_id': None,
								'quantity': min_qty,
								'price': price
							})
					else:
						# For each variant
						for variant in product_in_ctx.product_variant_ids:
							price = round(variant.price, self._prices_precision)
							# If price is not 0 and not in prices list yet
							product_filter = filter(lambda x: x['pricelist_id'] == pricelist.id and x['product_id'] == product_id and x['variant_id'] == variant.id and x['quantity'] == min_qty and x['price'] == price, prices)
							if price and not bool(list(product_filter)):
								prices.append({ 
									'pricelist_id': pricelist.id,
									'product_id': product_in_ctx.id,
									'variant_id': variant.id,
									'quantity': min_qty,
									'price': price
								})

		# Send to JSync
		if prices:
			packet = JSync()
			packet.name = 'pricelist_item'
			packet.data = prices
			packet.send(action='replace')

		self.write_to_log('[b2b_pricelists_prices] Ends!')

	def b2b_customers_prices(self):
		self.write_to_log('[b2b_customers_prices] Starts!')
		# Out prices
		prices = list()

		# Get all prices
		for price_line in self.env['customer.price'].read_group([], ('partner_id', 'product_tmpl_id', 'product_id', 'min_qty', 'price'), groupby=('partner_id', 'product_tmpl_id', 'product_id', 'min_qty'), orderby=('id DESC'), lazy=False):
			if price_line.get('price') and (price_line.get('product_tmpl_id') or price_line.get('product_id')):
				# Get product ID's
				template_id = price_line['product_tmpl_id'][0] if price_line.get('product_tmpl_id') else None
				variant_id = price_line['product_id'][0] if price_line.get('product_id') else None
				# Unify quantities (0 and 1)
				line_quantity = price_line['min_qty'] if price_line['min_qty'] > 1 else 1
				# If price is related to variant get template id
				if not template_id:
					template_id = self.env['product.product'].browse(variant_id).product_tmpl_id.id
				# Check if rule exists
				price_found = bool(list(filter(lambda x: x['customer_id'] == price_line['partner_id'][0] and x['product_id'] == template_id and x['variant_id'] == variant_id and x['quantity'] == line_quantity, prices)))
				# Add price
				if not price_found:
					prices.append({ 
						'customer_id': price_line['partner_id'][0],
						'product_id': template_id,
						'variant_id': variant_id,
						'quantity': line_quantity,
						'price': round(price_line['price'], self._prices_precision)
					})

		# Send to JSync
		if prices:
			packet = JSync()
			packet.name = 'customer_price'
			packet.data = prices
			packet.send(action='replace')

		self.write_to_log('[b2b_customers_prices] Ends!')

	def b2b_products_stock(self, test_limit=None, test_date=None):
		self.write_to_log('[b2b_products_stock] Starts!')
		# Out stock
		stock = list()
		# Time now
		start_date = datetime.now()
		# Last time executed
		last_date = test_date or self.env['b2b.settings'].get_default_params().get('last_stock_date', False)
		# Search params
		product_search_params = [('website_published', '=', True)]
		# All stock moves
		if last_date:
			self.env.cr.execute(
				"SELECT product_tmpl_id FROM product_product \
					WHERE id IN ( \
						SELECT product_id FROM stock_move WHERE \
						write_date > %s \
						GROUP BY product_id \
							UNION \
						SELECT product_id FROM sale_order_line WHERE \
						write_date > %s \
						GROUP BY product_id \
					) \
				GROUP BY product_tmpl_id", 
			[last_date, last_date])
			# Limit search to products with stock moves 
			product_ids = [r[0] for r in self.env.cr.fetchall()]
			product_search_params.append(('id', 'in', product_ids))
		# Filtered products
		products_ids = self.env['product.template'].search(product_search_params, limit=test_limit).ids
		# Log info
		product_number = 0.0
		total_products = len(products_ids)
		self.write_to_log('# PRODUCTOS: %s' % total_products)
		# For each product
		for product_id in products_ids:
			product_number += 1
			percent = round((product_number / total_products) * 100, 2)
			product = self.env['product.template'].browse(product_id)
			self.write_to_log(":: %s%% PROCESANDO... [%s] %s" % (percent, product.default_code, product.name))
			for variant in product.product_variant_ids:
				stock.append({ 
					'product_id': variant.product_tmpl_id.id,
					'variant_id': variant.id if variant.product_attribute_count else None,
					'stock': variant.web_global_stock
				})

		# Send to JSync
		if stock:
			packet = JSync()
			packet.name = 'product_stock'
			packet.data = stock
			packet.send(action='update_batch_public' if last_date else 'replace')

		# Update last stock date
		if not test_date:
			self.env['b2b.settings'].set_param('last_stock_date', start_date)

		self.write_to_log('[b2b_products_stock] Ends!')
