# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import logging
import base64
import re

_logger = logging.getLogger('B2B-OUT')

class B2bItemsOut(models.Model):
	_name = 'b2b.item.out'
	_description = 'B2B Item Out'
	_order = 'sequence, id'
	_sql_constraints = [('b2b_item_out_unique', 'unique(name)', 'Name must be unique into B2B Outgoing Items!')]

	_default_code_str = re.sub(r'(^[ ]{0,8})', '', """
        # Set to None for watch all
        fields_to_watch = ('name', 'reference')

        # When this model is notifiable
        def is_notifiable(self, action, vals):
            return True

        # Set the model and related record for a cascade delete
        def related_to(self, action):
            return None

        # Object data to send
        def get_data(self, action):
            return {
                'jim_id': self.id, # Item key (required)
                'name': self.get_field_translations('name'),
                'category_id': self.categ_id.id if self.categ_id else None
            }
	""", flags=re.M).strip()

	sequence = fields.Integer(help="Determine the items order")
	name = fields.Char('Item Name', required=True, translate=False, help="Set the item name", index=True)
	model = fields.Char('Model Names', required=True, translate=False, help="Odoo model names to check separated by , or ;")
	description = fields.Char('Description', required=False, translate=False, help="Set the item description")
	code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
	active = fields.Boolean('Active', default=True, help="Enable or disable this item")
	exclude_on_sync = fields.Boolean('Exclude on syncing', default=False, help="Exclude for sync action")
	sync_updates = fields.Boolean('Updates on sync', default=True, help="Send updates on syncing")
	
	@api.multi
	def get_models(self):
		"""
		Get item models list
		"""
		self.ensure_one()
		separators = (',', ';')
		models = set()

		for separator in separators:
			if separator in self.model:
				for model in self.model.split(separator):
					models.add(model.strip())

		if not models:
			models.add(self.model.strip())

		return list(models)

	@api.model
	def __check_model(self):
		"""
		Check if is a valid model or models
		"""
		for model_name in self.get_models():
			if not model_name in self.env:
				raise UserError(_('Model %s not found!') % model_name)

	@api.model
	def __check_code(self):
		"""
		Check if is a valid code
		"""
		try:
			exec(self.code, locals())
		except Exception as e:
			raise UserError(_('Syntax Error?\n') + str(e))
		# Check required vars and methods to avoid fatal errors
		variables = { 'fields_to_watch': (list, tuple) }
		methods = ['is_notifiable', 'get_data']
		for var in tuple(variables.keys() + methods):
			if not var in locals():
				raise UserError(_('Code Error!\n %s not defined' % (var)))
		for var, typ in variables.items():
			var_content = eval(var)
			if var_content and type(var_content) not in typ:
				raise UserError(_('Code Error!\nItem: %s\nVar name: %s\nReceived type: %s\nExpected type: %s' % (self.name, var, type(var_content), typ)))
		for method in methods:
			if not callable(eval(method)):
				raise UserError(_('Code Error!\n %s must be a function' % (method)))

	@api.model
	def evaluate(self, mode='create', config=dict(), **kwargs):
		b2b = dict()
		b2b['logger'] = _logger
		b2b['crud_mode'] = mode
		b2b['images_base'] = config.get('base_url')
		b2b['min_docs_date'] = config.get('docs_after')
		# Actualizamos con kwargs
		if kwargs: b2b.update(kwargs)
		# Librerías permitidas en el código
		from datetime import datetime
		# Ejecutamos el código con exec(item.code)
		exec(self.code, locals(), b2b)
		# Devolvemos la variable b2b
		return b2b

	@api.one
	def sync_item(self, user_notify=False):
		"""
		Sync all model records
		"""
		only_active = True # Get archived items
		search_query = [] # Default query
		record_number = 0.0 # Record counter

		# Documents min date
		docs_min_date = self.env['b2b.settings'].get_param('docs_after')

		# Clients on Jsync
		client_ids = [int(x.split(',')[1]) for x in self.env['b2b.export'].search([('name', '=', 'customer')]).mapped('res_id')]

		for model in self.get_models():
			if not self.exclude_on_sync:
				# Model specific queries
				if model == 'stock.move':
					# Movimientos de stock de Jim y EME que tienen un alabarán de origen (group_id) y la fecha es igual o superior a la actual y el estado es asignado
					search_query = [('company_id', 'in', [1, 11]), ('group_id', '!=', False), ('date_expected', '>=', str(datetime.now()))]
				elif model == 'res.partner':
					# Direcciones o clientes empresa
					search_query = ['|', ('type', '=', 'delivery'), ('is_company', '=', True)]
				elif model == 'account.invoice':
					# Facturas de clientes que se exportaron
					search_query = [('date_invoice', '>=', docs_min_date), ('commercial_partner_id', 'in', client_ids)]
				elif model == 'stock.picking':
					# Los albarares no se filtran por el cliente, ya que
					# pueden ser de DROPSIPPING y no ser notificables
					search_query = [('date_done', '>=', docs_min_date)]
				elif model == 'sale.order':
					# Pedidos de venta con fecha igual o superior a la establecida de clientes que se exportaron
					search_query = [('date_order', '>=', docs_min_date), ('partner_id.commercial_partner_id', 'in', client_ids)]
				elif model in ('product.template', 'product.product', 'product.tag'):
					# Todos los registros (activos e inactivos)
					only_active = False

				# Get code model records
				records_ids = self.env[model].with_context(active_test=only_active).search(search_query, order='id ASC').ids
				total_records =  len(records_ids)
				create_records = 0
				update_records = 0
				delete_records = 0

				_logger.info("*************** B2B ITEM ***************")
				_logger.info("@@ ITEM NAME: %s" % str(self.name))
				_logger.info("@@ ITEM MODEL: %s" % str(model))
				_logger.info("@@ TOTAL RECORDS: %s" % total_records)

				for id in records_ids:
					record_number += 1
					record_percent = round((record_number / total_records) * 100, 1)
					record_percent_str = str(record_percent) + '%'
					record = self.env[model].browse(id)
					res_id = '%s,%s' % (record._name, record.id)
					notifiable_items = record.is_notifiable_check()
					notifiable_values = notifiable_items.values()
					record_on_jsync = self.env['b2b.export'].search([('res_id', '=', res_id)], limit=1)

					if all(notifiable_values) and not record_on_jsync:

						create_records += 1
						_logger.info("@@ CREATE %s (%s) WITH ID#%s | COMPLETED: %s" % (self.name, model, id, record_percent_str))
						record.b2b_record('create', user_notify=user_notify)

					elif not all(notifiable_values) and record_on_jsync:

						delete_records += 1
						_logger.info("@@ DELETE %s (%s) WITH ID#%s | COMPLETED: %s" % (self.name, model, id, record_percent_str))
						record.b2b_record('delete', user_notify=user_notify)

					elif all(notifiable_values) and self.sync_updates:

						update_records += 1
						_logger.info("@@ UPDATE %s (%s) WITH ID#%s | COMPLETED: %s" % (self.name, model, id, record_percent_str))
						record.b2b_record('update', user_notify=user_notify)

					else:

						_logger.info("@@ %s (%s) ID#%s NOT NOTIFIABLE | COMPLETED: %s" % (self.name, model, id, record_percent_str))

				_logger.info("@@ CREATE RECORDS: %s" % create_records)
				_logger.info("@@ UPDATE RECORDS: %s" % update_records)
				_logger.info("@@ DELETE RECORDS: %s" % delete_records)

				# Notify user
				self.env.user.notify_info(
					_('Synchronizing <b>%s</b><br/> \
					<ul> \
						<li>Total: %s</li> \
						<li>Create: %s</li> \
						<li>Update: %s</li> \
						<li>Delete: %s</li> \
					</ul>') % (self.name, total_records, create_records, update_records, delete_records)
				)

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		"""
		Check model & code on create
		"""
		item = super(B2bItemsOut, self).create(vals)
		item.__check_model()
		item.__check_code()
		return item

	@api.multi
	def write(self, vals):
		"""
		Check model & code on write
		"""
		self.invalidate_cache()
		res = super(B2bItemsOut, self).write(vals)
		for item in self:
			if vals.get('model') or vals.get('active') == True:
				item.__check_model()
			if vals.get('code'):
				item.__check_code()
		return res