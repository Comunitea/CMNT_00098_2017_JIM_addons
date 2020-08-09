# -*- coding: utf-8 -*-
from odoo import http
import logging
import json

_logger = logging.getLogger('B2B-INCOMING')

class B2bController(http.Controller):

	@http.route([
		'/b2b_incoming'
	], type='http', auth='user', methods=['GET',])
	def index(self, **kw):

		# B2B In Active Items
		return http.request.render('js_b2b.b2b_in_home', {
			'b2b_in_active': http.request.env['b2b.item.in'].search([('active', '=', True)]),
			'b2b_in_inactive': http.request.env['b2b.item.in'].search([('active', '=', False)])
		})

	@http.route([
		'/b2b_incoming'
	], type='json', auth='user', methods=['POST',])
	def message(self, **kw):

		try:
			# Process message
			data_obj = http.request.params
			item_user = data_obj.get('user_id', 0)
			item_company = data_obj.get('company_id', 0)
			item_name = data_obj.get('object')
			item_action = data_obj.get('action', 'create')
			item_data = data_obj.get('data')

			# Debug data
			debug_str = "Message: " \
					"\n    - name: {}" \
					"\n    - user: {}" \
					"\n    - company: {}" \
					"\n    - operation: {}" \
					"\n    - data: {}".format(item_name, item_user, item_company, item_action, item_data)

			# Process item
			if http.request.env['b2b.item.in'].must_process(item_name, item_user, item_company, item_data, item_action):

				# OK
				_logger.info(debug_str)
				return 'OK'

			else:

				# ERROR
				_logger.critical(debug_str)
				return 'ERROR 500'

		except ValueError:

			# Invalid JSON
			_logger.error("Invalid JSON received")
			return 'ERROR 400'

	@http.route([
		'/jesie_to_b2b_sync'
	], type='http', auth='user')
	def run(self, execute=0, **kw):

		if http.request.env.user.has_group('base.group_system'):

			products_to_publish = 0
			products_to_unpublish = 0
			variants_to_publish = 0
			variants_to_unpublish = 0

			# Buscamos en los productos archivados también por si hay que despublicar alguno
			for product in http.request.env['product.template'].with_context(active_test=False).search([]):

				product_published = bool(product.website_published)
				# Condiciones de Jesie, que la etiqueta no sea la 50 es un añadido pues esos en Jesie se enviaban pero estaban ocultos
				product_must_be_published = bool(product.active and product.type == 'product' and product.tag_ids and 50 not in product.tag_ids.ids and product.sale_ok and product.default_code and product.default_code.find('False') == -1 and product.name.find('(copia)') == -1)

				if not product_published and product_must_be_published:
					# En Jesie está publicado
					product_published = True
					products_to_publish += 1
				elif product_published and not product_must_be_published:
					# En Jesie no está publicado
					product_published = False
					products_to_unpublish += 1

				if execute and product_published != product.website_published:
					# No lo evaluamos para que sea más rápido por lo que si hay cambios deberemos
					# hacer una sincronización de productos a posterior
					product.with_context(b2b_evaluate=False).website_published = product_published

				for variant in product.product_variant_ids:

					variant_published = bool(variant.website_published)
					# Condiciones de Jesie para que la variante sea notificable
					variant_must_be_published = bool(variant.active and variant.default_code and variant.force_web != 'no')

					if not product_published and variant_published:
						# En Jesie está publicada
						variant_published = False
						variants_to_unpublish += 1
					elif product_published and not variant_published and variant.active and not variant.attribute_names:
						# La variante única siempre se publica
						variant_published = True
						variants_to_publish += 1
					elif product_published and not variant_published and variant_must_be_published:
						# En Jesie no está publicada
						variant_published = True
						variants_to_publish += 1

					if execute and variant_published != variant.website_published:
						# No lo evaluamos para que sea más rápido por lo que si hay cambios deberemos
						# hacer una sincronización de variantes a posterior
						variant.with_context(b2b_evaluate=False).website_published = variant_published

			message = 'Para hacer efectivos los cambios lanzar con execute=1' if not execute else '¡Realizado! Si hay cambios tendrás que hacer una sincronización'

			return '''
				<h2>JESIE TO B2B SYNC</h2>
				<hr/>
				<h2>PRODUCTOS</h2>
				<p>PUBLICAR: %s</p>
				<p>ELIMINAR: %s</p>
				<h2>VARIANTES</h2>
				<p>PUBLICAR: %s</p>
				<p>ELIMINAR: %s</p>
				<pre>%s</pre>
			''' % (products_to_publish, products_to_unpublish, variants_to_publish, variants_to_unpublish, message)

		else:

			return 'No está autorizado para acceder a esta página'

	@http.route([
		'/js_addons_web_companies_to_b2b'
	], type='http', auth='user')
	def run(self, execute=0, **kw):

		if http.request.env.user.has_group('base.group_system'):

			if execute:
				# Eliminar datos de la tabla res_partner_res_company_web_access (vip_web_access)
				http.request.env.cr.execute("TRUNCATE res_partner_res_company_web_access RESTART IDENTITY")

				""" Copiar valores de res_partner_res_company_rel (group_companies_ids) a res_partner_res_company_web_access (vip_web_access)
				omitiendo las empresas en las que el cliente no tiene tarifa """
				http.request.env.cr.execute("INSERT INTO res_partner_res_company_web_access \
					(SELECT res_partner_id, res_company_id FROM res_company_res_partner_rel \
					LEFT JOIN ir_property ON ir_property.res_id = 'res.partner,' || res_partner_id AND ir_property.company_id = res_company_id AND name LIKE 'property_product_pricelist' \
					WHERE ir_property.id IS NOT NULL \
					GROUP BY res_partner_id, res_company_id)")

			return '¡LISTO!' if execute else 'EMM... ¡FALTA ALGO!'

		else:

			return 'No está autorizado para acceder a esta página'