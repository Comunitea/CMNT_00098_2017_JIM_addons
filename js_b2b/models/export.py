# -*- coding: utf-8 -*-
from odoo import api, fields, models
from ..base.helper import JSync

class B2BBulkExport(models.Model):
	_name = "b2b.export"

	_prices_precision = 2

	def __pricelists_unique_quantities(self):
		unique_quantities = self.env['product.pricelist.item'].read_group([], ('min_quantity'), groupby=('min_quantity'), orderby=('min_quantity ASC'), lazy=True)
		unique_quantities = [qty['min_quantity'] for qty in unique_quantities]
		# Remove 0 from quantities if exists
		if 0 in unique_quantities:
			unique_quantities.remove(0)
		# Remove 1 from quantities if exists
		if 1 in unique_quantities:
			unique_quantities.remove(1)
		# Return tuple
		return tuple(unique_quantities)

	def b2b_pricelists_prices(self, test_limit=None):
		# Out prices
		prices = list()
		# All pricelists
		pricelists = self.env['product.pricelist'].search([('active', '=', True)])
		# All products
		products = self.env['product.template'].search([('type', 'like', 'product'), ('tag_ids', '!=', False), ('sale_ok', '=', True)], limit=test_limit)
		# All quantities
		quantities = self.__pricelists_unique_quantities()
		# For each pricelist
		for p in pricelists:
			# All products
			for product in products:
				# Product in pricelist context
				product = product.with_context(pricelist=p.name)
				# Get all variant prices
				variants_prices = product.product_variant_ids.mapped('price')
				# Same price in all variants
				price_on_template = all(x==variants_prices[0] for x in variants_prices if variants_prices[0])

				if price_on_template:
					# Get unit price
					unit_price = product.product_variant_id.price
					# Set unit data
					price_data = { 
						'pricelist_id': p.id,
						'product_id': product.id,
						'variant_id': None,
						'quantity': 1,
						'price': round(unit_price, self._prices_precision)
					}

					# Add price
					if unit_price:
						prices.append(price_data)

					# Check price for quantities
					for min_qty in quantities:
						# Get price for this quantity
						qty_price = product.with_context(quantity=min_qty).price
						# If not same price
						if qty_price != unit_price:
							price_data.update({ 'quantity': min_qty, 'price': round(qty_price, self._prices_precision) })
							# Add price
							prices.append(price_data)
				else:
					# For each variant
					for variant in product.product_variant_ids:
						# Get unit price
						unit_price = variant.price
						# Set unit data
						price_data = { 
							'pricelist_id': p.id,
							'product_id': product.id,
							'variant_id': variant.id,
							'quantity': 1,
							'price': round(unit_price, self._prices_precision)
						}

						# Add price
						if unit_price:
							prices.append(price_data)

						# Check price for quantities
						for min_qty in quantities:
							# Get price for this quantity
							qty_price = variant.with_context(quantity=min_qty).price
							# If not same price
							if qty_price != unit_price:
								price_data.update({ 'quantity': min_qty, 'price': round(qty_price, self._prices_precision) })
								# Add price
								prices.append(price_data)

		# Send to JSync
		packet = JSync()
		packet.name = 'pricelist_item'
		packet.data = prices
		packet.send(action='replace')

	def b2b_customers_prices(self):
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
				price_found = next(price for item in prices if prices['customer_id'] == price_line['partner_id'][0] and prices['product_id'] == template_id and prices['variant_id'] == variant_id and prices['quantity'] == line_quantity)
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

	def b2b_products_stock(self):
		# Out stock
		stock = list()