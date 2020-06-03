# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.queue_job.job import job
from ..base.helper import JSync
from os import path, pardir
from datetime import datetime
import psycopg2.extras

class B2BBulkExport(models.Model):
	_name = "b2b.export"

	_log_filename = 'b2b.export.log'

	# ------------------------------------ LOGGER ------------------------------------

	def write_to_log(self, txt, file=None, mode="aw+"):
		module_dir = path.abspath(path.join(path.dirname(path.realpath(__file__)), pardir))
		log_file = path.join(module_dir, 'static', 'log', file or self._log_filename)
		with open(log_file, mode) as file:
			date = fields.Datetime.now()
			file.write("%s %s\n" % (date, txt))
			print("%s %s" % (date, txt))

	# ------------------------------------ CUSTOM QUERIES ------------------------------------

	def __pricelists_unique_quantities(self):
		self.env.cr.execute("SELECT pricelist_id, \
			CASE \
				WHEN min_quantity > 0 THEN min_quantity \
				ELSE 1 \
			END min_qty \
			FROM product_pricelist_item  \
			WHERE pricelist_id IS NOT NULL  \
			AND active = true \
			GROUP BY pricelist_id, min_qty \
			ORDER BY pricelist_id, min_qty")
		return self.env.cr.fetchall()

	def __products_in_pricelists(self):
		self.env.cr.execute("SELECT product_tmpl_id \
			FROM product_product \
			WHERE id IN ( \
				SELECT product_id FROM product_pricelist_item \
				WHERE active = true \
				GROUP BY product_id \
			) OR product_tmpl_id IN ( \
				SELECT product_tmpl_id FROM product_pricelist_item \
				WHERE active = true \
				GROUP BY product_tmpl_id \
			) \
			GROUP BY product_tmpl_id")
		return tuple(r[0] for r in self.env.cr.fetchall())

	"""def __products_with_stock_moves(self, date=None):
		self.env.cr.execute("SELECT product_tmpl_id \
			FROM product_product \
			WHERE id IN ( \
				SELECT product_id FROM stock_move WHERE \
				write_date > %s \
				GROUP BY product_id \
					UNION \
				SELECT product_id FROM sale_order_line WHERE \
				write_date > %s \
				GROUP BY product_id \
					UNION \
				SELECT product_id FROM stock_quant WHERE \
				write_date > %s \
				GROUP BY product_id \
			) \
			GROUP BY product_tmpl_id", [date, date, date])
		return tuple(r[0] for r in self.env.cr.fetchall())

	def _pricelists_prices_to_update(self, replace=False, limit='ALL'):
		self.env.cr.execute("SELECT \
				export_prices.pricelist_id, \
				product_product.product_tmpl_id AS product_id, \
				CASE \
					WHEN product_product.attribute_names <> '' THEN product_product.id \
					ELSE NULL \
				END variant_id, \
				CASE \
					WHEN export_prices.qty > 0 THEN export_prices.qty \
					ELSE 1 \
				END quantity, \
				export_prices.price \
			FROM export_prices \
			LEFT JOIN product_product ON export_prices.product_id = product_product.id \
			WHERE create_mode = %r \
			GROUP BY export_prices.id, export_prices.pricelist_id, product_product.product_tmpl_id, product_product.id, export_prices.qty \
			ORDER BY export_prices.id ASC \
			LIMIT %s" % (replace, limit))
		return self.env.cr.dictfetchall()"""

	# ------------------------------------ STATIC METHODS ------------------------------------

	@staticmethod
	def is_time_between(begin_time, end_time, check_time=None):
		# If check time is not given, default to current UTC time
		check_time = check_time or datetime.now().strftime("%H:%M:%S")
		if begin_time < end_time:
			return check_time >= begin_time and check_time <= end_time
		else: # crosses midnight
			return check_time >= begin_time or check_time <= end_time

	# ------------------------------------ PUBLIC METHODS ------------------------------------

	"""def b2b_pricelists_prices(self, test_limit=None):
		# Get calculated prices to replace
		r_prices = self._pricelists_prices_to_update(True, test_limit or 'ALL')
		print("::::::::::: REPLACE PRICES", r_prices)

		# Send to JSync
		if r_prices:
			packet = JSync(settings=self.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error']))
			packet.name = 'pricelist_item'
			packet.data = r_prices
			packet.mode = 'replace'
			packet.send(timeout_sec=300)
			self.write_to_log(str(r_prices), 'pricelist_item_replace', "w+")
			self.env['export.prices'].search([('create_mode', '=', True)]).unlink()

		# Get calculated prices to update
		u_prices = self._pricelists_prices_to_update(False, test_limit or 'ALL')
		print("::::::::::: UPDATE PRICES", u_prices)

		# Send to JSync
		if u_prices:
			packet = JSync(settings=self.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error']))
			packet.name = 'pricelist_item'
			packet.data = u_prices
			packet.mode = 'update'
			packet.send(timeout_sec=300)
			self.write_to_log(str(u_prices), 'pricelist_item_update', "w+")
			self.env['export.prices'].search([('create_mode', '=', False)]).unlink()"""

	@job
	def b2b_pricelists_prices(self, test_limit=None, templates_filter=None, variant=None, operation=None):
		self.write_to_log('[b2b_pricelists_prices] Starts!')
		# Out prices
		prices = list()
		# Get decimals number
		prices_precision = self.env['decimal.precision'].precision_get('Product Price')
		# Pricelist quantities search, returns a list of unique quantities for pricelist
		def _search_pricelist_quantities(quantities, pricelist_id):
			unique_quantities = set(tuple(qty[1] for qty in quantities if qty[0] == pricelist_id))
			# Add 1 on quantities if not exists
			if 1 not in unique_quantities:
				unique_quantities.add(1)
			# Return sorted tuple
			return sorted(tuple(unique_quantities))
		# All pricelists
		pricelists = tuple(self.env['product.pricelist'].search([('web', '=', True), ('active', '=', True)]).mapped(lambda p: (p.id, p.name, p.company_id.id)))
		# Search params
		product_search_params = [('website_published', '=', True)]
		# Limit search to this products
		product_ids = templates_filter or self.__products_in_pricelists()
		product_search_params.append(('id', 'in', product_ids))
		# All products
		products_ids = tuple(self.env['product.template'].search(product_search_params, limit=test_limit).ids)
		# All quantities
		quantities = self.__pricelists_unique_quantities()
		# Log info
		total_pricelists = len(pricelists)
		total_products = len(products_ids)
		product_number = 0.0
		self.write_to_log('# LISTAS DE PRECIOS: %s' % total_pricelists)
		self.write_to_log('# PRODUCTOS: %s' % total_products)

		try:
			# For each product
			for product_id in products_ids:
				product_number += 1
				percent = round((product_number / total_products) * 100, 1)
				product = self.env['product.template'].browse(product_id)
				print("---------------------------------------------------------------------------")
				print(":: %s%% PROCESANDO... [%s] %s" % (percent, product.default_code, product.name))
				print("---------------------------------------------------------------------------")
				print(":: %10s\t%10s\t%6s\t%8s" % ('PRICELIST', 'VARIANT', 'QTY', 'PRICE'))
				# For each pricelist
				for pricelist in pricelists:
					# For each quantity
					for min_qty in _search_pricelist_quantities(quantities, pricelist[1]):
						# Product in pricelist & qty context
						product_in_ctx = product.with_context({ 'pricelist': pricelist[1], 'quantity': min_qty })
						# Get all variant prices
						variants_prices = tuple(product_in_ctx.product_variant_ids.mapped('price'))
						# Same price in all variants
						if all(x==variants_prices[0] for x in variants_prices if variants_prices[0]):
							price = None if operation == 'delete' and not variant else round(variants_prices[0], prices_precision)
							# If price is not 0 and not in prices list yet with qty 1
							product_filter = filter(lambda x: x['pricelist_id'] == pricelist[0] and x['product_id'] == product_id and x['variant_id'] == None and x['quantity'] == 1 and x['price'] == price, prices)
							if not bool(list(product_filter)):
								print(":: %10s\t%10s\t%6s\t%8s" % (pricelist[0], '-', min_qty, price))
								prices.append({ 
									'company_id': pricelist[2] or None,
									'pricelist_id': pricelist[0],
									'product_id': product_id,
									'variant_id': None,
									'quantity': min_qty,
									'price': price
								})
						else:
							# For each variant
							for v in range(len(variants_prices)):
								variant_id = product_in_ctx.product_variant_ids.ids[v]
								price = None if operation == 'delete' and variant_id == variant else round(variants_prices[v], prices_precision)
								# If price is not 0 and not in prices list yet with qty 1
								product_filter = filter(lambda x: x['pricelist_id'] == pricelist[0] and x['product_id'] == product_id and x['variant_id'] == variant_id and x['quantity'] == 1 and x['price'] == price, prices)
								if not bool(list(product_filter)) and (operation == 'delete' or price):
									print(":: %10s\t%10s\t%6s\t%8s" % (pricelist[0], variant_id, min_qty, price))
									prices.append({ 
										'company_id': pricelist[2] or None,
										'pricelist_id': pricelist[0],
										'product_id': product_id,
										'variant_id': variant_id,
										'quantity': min_qty,
										'price': price
									})
		except Exception as e:
			self.write_to_log('[b2b_pricelists_prices] ERROR ON LOOP! %s' % e)
		finally:
			self.write_to_log('[b2b_pricelists_prices] Ends!')

		# Send to JSync
		if prices:
			packet = JSync(settings=self.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error']))
			packet.name = 'pricelist_item'
			packet.data = prices
			packet.mode = 'update' if templates_filter is not None else 'replace'
			packet.send(timeout_sec=300)
			self.write_to_log(str(prices), 'pricelist_item', "w+")

	@job
	def b2b_customers_prices(self, lines_filter=None, operation=None):
		self.write_to_log('[b2b_customers_prices] Starts!')
		# Out prices
		prices = list()
		# Get decimals number
		prices_precision = self.env['decimal.precision'].precision_get('Product Price')
		# Price lines filter
		prices_filter = [('id', 'in', lines_filter)] if lines_filter and type(lines_filter) is list else list()
		try:
			# Get all prices
			for price_line in self.env['customer.price'].read_group(prices_filter, ('company_id', 'partner_id', 'product_tmpl_id', 'product_id', 'min_qty', 'price'), groupby=('company_id', 'partner_id', 'product_tmpl_id', 'product_id', 'min_qty'), orderby=('id DESC'), lazy=False):
				if 'price' in price_line and (price_line.get('product_tmpl_id') or price_line.get('product_id')):
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
					if not price_found and (operation == 'delete' or price_line['price']):
						prices.append({ 
							'company_id': price_line['company_id'][0] if price_line['company_id'] else None,
							'customer_id': price_line['partner_id'][0],
							'product_id': template_id,
							'variant_id': variant_id,
							'quantity': line_quantity,
							'price': round(price_line['price'] if operation != 'delete' else None, prices_precision)
						})
		except Exception as e:
			self.write_to_log('[b2b_customers_prices] ERROR ON LOOP! %s' % e)
		finally:
			self.write_to_log('[b2b_customers_prices] Ends!')

		# Send to JSync
		if prices:
			packet = JSync(settings=self.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error']))
			packet.name = 'customer_price'
			packet.data = prices
			packet.mode = 'update' if lines_filter is not None else 'replace'
			packet.send(timeout_sec=300)
			self.write_to_log(str(prices), 'customer_price', "w+")

	@job
	def b2b_products_stock(self, test_limit=None, test_date=None):
		# If actual time is between 00:30 & 00:45 set "all" to True
		all_products = B2BBulkExport.is_time_between('00:30:00', '00:45:00')
		print(":::::: ALL PRODUCTS", all_products)
		stock = self.env['exportxml.object'].compute_product_ids(all=True, from_time=test_date, inc=test_limit or 999999999)

		# Send to JSync
		if stock:
			packet = JSync(settings=self.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error']))
			packet.name = 'product_stock'
			packet.data = stock
			packet.mode = 'replace' if all_products else 'update'
			if packet.send(timeout_sec=300):
				self.write_to_log(str(stock), 'product_stock', "w+")

	"""def b2b_products_stock(self, test_limit=None, test_date=None):
		self.write_to_log('[b2b_products_stock] Starts!')
		# Out stock
		stock = list()
		# Time now
		start_date = fields.Datetime.now()
		# Last time executed
		last_date = test_date or self.env['b2b.settings'].get_default_params().get('last_stock_date', False)
		# Search params
		product_search_params = [('website_published', '=', True)]
		# All stock moves
		if last_date:
			# Limit search to products with stock moves 
			product_ids = self.__products_with_stock_moves(last_date)
			product_search_params.append(('id', 'in', product_ids))
		# Filtered products
		products_ids = tuple(self.env['product.template'].search(product_search_params, limit=test_limit).ids)
		# Log info
		product_number = 0.0
		total_products = len(products_ids)
		self.write_to_log('# PRODUCTOS: %s' % total_products)

		try:
			# For each product
			for product_id in products_ids:
				product_number += 1
				percent = round((product_number / total_products) * 100, 1)
				product = self.env['product.template'].browse(product_id)
				print(":: %s%% PROCESANDO... [%s] %s" % (percent, product.default_code, product.name))
				for variant in product.product_variant_ids:
					stock_for_product = variant.web_global_stock
					stock.append({ 
						'product_id': variant.product_tmpl_id.id,
						'variant_id': variant.id if variant.product_attribute_count else None,
						'stock': stock_for_product if stock_for_product > 0 else 0
					})
		except Exception as e:
			self.write_to_log('[b2b_products_stock] ERROR ON LOOP! %s' % e)
		finally:
			self.write_to_log('[b2b_products_stock] Ends!')

		# Send to JSync
		if stock:
			packet = JSync(settings=self.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error']))
			packet.name = 'product_stock'
			packet.data = stock
			packet.mode = 'update' if last_date else 'replace'
			packet.send(timeout_sec=300)
			self.write_to_log(str(stock), 'product_stock', "w+")

		# Update last stock date
		if start_date and not test_date:
			self.env['b2b.settings'].update_param('last_stock_date', start_date)
	"""