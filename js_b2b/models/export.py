# -*- coding: utf-8 -*-
from odoo import api, fields, models
from ..base.helper import JSync
import datetime
import os

class B2BBulkExport(models.Model):
	_name = "b2b.export"

	_prices_precision = 2
	_log_filename = 'b2b.export.log'

	def write_to_log(self, txt):
		module_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
		log_file = os.path.join(module_dir, 'static', 'log', self._log_filename)
		with open(log_file, "aw+") as file:
			date = datetime.datetime.now()
			file.write("%s %s\n" % (date, txt))
			print("%s %s\n" % (date, txt))

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
		products = self.env['product.template'].search([('type', 'like', 'product'), ('tag_ids', '!=', False), ('sale_ok', '=', True)], limit=test_limit)
		# All quantities
		quantities = self.__pricelists_unique_quantities()
		# Log info
		total_pricelists = len(pricelists)
		total_products = len(products)
		product_number = 0.0
		self.write_to_log('# LISTAS DE PRECIOS: %s' % total_pricelists)
		self.write_to_log('# PRODUCTOS: %s' % total_products)
		self.write_to_log('# CANTIDADES A CALCULAR: %s' % quantities)
		# For each pricelist
		for pricelist in pricelists:
			# For each product
			for product in products:
				product_number += 1
				# For each quantity
				for min_qty in quantities:
					# Product in pricelist & qty context
					product_in_ctx = product.with_context({ 'pricelist': pricelist.name, 'quantity': min_qty })
					# Get all variant prices
					variants_prices = product_in_ctx.product_variant_ids.mapped('price')
					# Same price in all variants
					if all(x==variants_prices[0] for x in variants_prices if variants_prices[0]):
						price = round(product_in_ctx.product_variant_id.price, self._prices_precision)
						price_in_list = bool(list(filter(lambda x: x['pricelist_id'] == pricelist.id and x['product_id'] == product.id and x['variant_id'] == None and x['quantity'] == 1 and x['price'] == price, prices)))
						# If price is not 0 and not in prices with min quantity = 1
						if price and not price_in_list:
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
							price_in_list = bool(list(filter(lambda x: x['pricelist_id'] == pricelist.id and x['product_id'] == product.id and x['variant_id'] == variant.id and x['quantity'] == 1 and x['price'] == price, prices)))
							# If price is not 0 and not in prices with min quantity = 1
							if price and not price_in_list:
								prices.append({ 
									'pricelist_id': pricelist.id,
									'product_id': product_in_ctx.id,
									'variant_id': variant.id,
									'quantity': min_qty,
									'price': price
								})

				products_percent = round(((product_number / total_products) * 100) / total_pricelists, 1)
				self.write_to_log('COMPLETADO %s%%' % products_percent)

		# Send to JSync
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
		packet = JSync()
		packet.name = 'customer_price'
		packet.data = prices
		packet.send(action='replace')
		self.write_to_log('[b2b_customers_prices] Ends!')

	def b2b_products_stock(self):
		# Out stock
		stock = list()