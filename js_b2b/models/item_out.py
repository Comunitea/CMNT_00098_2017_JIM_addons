# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import re

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
                # Item key (required)
                # fixed: modifier forces send even if it has not changed
                'fixed:jim_id': self.id,
                # Sends names dict when field has changed
                'name': self.get_field_translations('name'),
                # field: modifier sends if field has changed, if not setted send null
                'categ_id:category_id': self.categ_id.id if self.categ_id else None
            }
	""", flags=re.M).strip()

	name = fields.Char('Item Name', required=True, translate=False, help="Set the item name", index=True)
	model = fields.Char('Model Names', required=True, translate=False, help="Odoo model names to check separated by , or ;")
	description = fields.Char('Description', required=False, translate=False, help="Set the item description")
	code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
	active = fields.Boolean('Active', default=True, help="Enable or disable this item")
	sequence = fields.Integer(help="Determine the items order")

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
	def evaluate(self, mode='create', config=dict()):
		b2b = dict()
		b2b['crud_mode'] = mode
		b2b['images_base'] = config.get('base_url')
		b2b['min_docs_date'] = config.get('docs_after')
		# Librerías permitidas en el código
		from datetime import datetime
		# Ejecutamos el código con exec(item.code)
		exec(self.code, locals(), b2b)
		# Devolvemos la variable b2b
		return b2b

	@api.one
	def sync_item(self, mode='create', user_notify=False):
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

		# These models should not be synchronized directly (CRONJOBS)
		excluded_models = ('customer.price', 'product.pricelist.item')

		for model in self.get_models():
			if model not in excluded_models:
				# Model specific queries
				if model == 'stock.move':
					search_query = ['&', '&', '&', ('state', 'in', ['assigned', 'done', 'cancel']), ('company_id', '=', 1), ('purchase_line_id', '!=', False), ('date_expected', '>=', str(datetime.now().date()))]
				elif model == 'res.partner':
					search_query = ['|', ('type', '=', 'delivery'), ('is_company', '=', True)]
				elif model == 'product.tag':
					search_query = ['|', ('active', '=', True), ('active', '=', False)]
				elif model == 'account.invoice':
					search_query = [('date_invoice', '>=', docs_min_date), ('commercial_partner_id', 'in', client_ids)]
				elif model == 'stock.picking':
					search_query = [('date_done', '>=', docs_min_date), ('partner_id.commercial_partner_id', 'in', client_ids)]
				elif model == 'sale.order':
					search_query = [('date_order', '>=', docs_min_date), ('partner_id.commercial_partner_id', 'in', client_ids)]
				elif model in ('product.template', 'product.product'):
					only_active = False

				# Get code model records
				records_ids = self.env[model].with_context(active_test=only_active).search(search_query, order='id ASC').ids
				total_records =  len(records_ids)
				create_records = 0
				delete_records = 0

				print("*************** B2B ITEM ***************")
				print("@@ ITEM NAME", str(self.name))
				print("@@ ITEM MODEL", str(model))
				print("@@ TOTAL RECORDS", total_records)

				for id in records_ids:
					record_number += 1
					record_percent = round((record_number / total_records) * 100, 1)
					record_percent_str = str(record_percent) + '%'
					record = self.env[model].browse(id)
					res_id = '%s,%s' % (record._name, record.id)
					notifiable_items = record.is_notifiable_check()
					record_on_jsync = self.env['b2b.export'].search([('res_id', '=', res_id)], limit=1)

					if notifiable_items and not record_on_jsync:

						create_records += 1
						print("@@ CREATE %s (%s) WITH ID#%s" % (self.name, model, id), record_percent_str)
						for packet in record.b2b_record('create', conf_items_before=notifiable_items, auto_send=False):
							packet.send(notify=user_notify) # Don't notify

					elif not notifiable_items and record_on_jsync:

						delete_records += 1
						print("@@ DELETE %s (%s) WITH ID#%s" % (self.name, model, id), record_percent_str)
						for packet in record.b2b_record('delete', conf_items_before=[record_on_jsync.name,], auto_send=False):
							packet.send(notify=user_notify) # Don't notify

					else:

						print("@@ %s (%s) ID#%s NOT NOTIFIABLE OR ALREDY IN JSYNC" % (self.name, model, id), record_percent_str)
						
				print("@@ CREATE RECORDS", create_records)
				print("@@ DELETE RECORDS", delete_records)
				print("************* FIN B2B ITEM *************")

				# Notify user
				self.env.user.notify_info(
					_('Synchronizing <b>%s</b><br/> \
					<ul> \
						<li>Total: %s</li> \
						<li>Create: %s</li> \
						<li>Delete: %s</li> \
					</ul>') % (self.name, total_records, create_records, delete_records)
				)

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		"""
		Check model & code on create
		"""
		item = super(B2bItemsOut, self).create(vals)
		# item.__check_model()
		item.__check_code()
		return item

	@api.multi
	def write(self, vals):
		"""
		Check model & code on write
		"""
		res = super(B2bItemsOut, self).write(vals)
		for item in self:
			if vals.get('model') or vals.get('active', item.active) == True:
				item.__check_model()
			if vals.get('code'):
				item.__check_code()
		return res