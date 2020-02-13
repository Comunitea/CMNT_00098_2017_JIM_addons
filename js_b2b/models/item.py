# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..base.helper import JSync
import re

class B2bItems(models.Model):
	_name = 'b2b.item'
	_description = 'B2B Item'
	_order = 'sequence, id'
	_sql_constraints = [('b2b_item_unique', 'unique(name)', 'Name must be unique into B2B Items!')]
	_default_code_str = re.sub(r'(^[ ]{0,8})', '', """
        # Set to None for watch all
        b2b_fields_to_watch = ('name', 'reference')
        
        def b2b_is_notifiable(self, vals):
            return True

        def b2b_get_data(self):
            return {
                # Sends names dict when field has changed
                'name': self.get_field_translations('name'),
                # fixed: modifier forces send even if it has not changed
                'fixed:reference': self.default_code,
                # field: modifier sends if field has changed, if not setted send null
                'categ_id:category_id': self.categ_id.id if self.categ_id else None,
                # upload: modifier uploads base64 image to public server and replaces this param with the URL
                'upload:logo': '/9j/4AAQSkZJRgABAQAAAQABAAD...'
            }
	""", flags=re.M).strip()

	name = fields.Char('Item Name', required=True, translate=False, help="Set the item name")
	model = fields.Char('Model Name', required=True, translate=False, help="Odoo model name")
	description = fields.Char('Description', required=False, translate=False, help="Set the item description")
	code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
	active = fields.Boolean('Active', default=True, help="Enable or disable this item")
	sequence = fields.Integer(help="Determine the items order")

	@api.model
	def __check_model(self):
		"""
		Check if is a valid model
		"""
		try:
			self.env[self.model].search_count([])
		except Exception as e:
			raise UserError(_('Model not found!'))

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
		variables = { 'b2b_fields_to_watch': tuple }
		methods = ['b2b_is_notifiable', 'b2b_get_data']
		for var in tuple(variables.keys() + methods):
			if not var in locals():
				raise UserError(_('Code Error!\n %s not defined' % (var)))
		for var, typ in variables.items():
			var_content = eval(var)
			if var_content and type(var_content) is not typ:
				raise UserError(_('Code Error!\nItem: %s\nVar name: %s\nReceived type: %s\nExpected type: %s' % (self.name, var, type(var_content), typ)))
		for method in methods:
			if not callable(eval(method)):
				raise UserError(_('Code Error!\n %s must be a function' % (method)))

	@api.model
	def must_notify(self, record, vals=None):
		"""
		Check if item record is notifiable
		"""
		# Default
		is_notifiable = True
		# Basic checks, model and code
		if record and self.model == record._name and type(self.code) is unicode:
			from datetime import datetime
			import base64
			# Ejecutamos el código con exec(self.code, locals())
			# establece localmente las siguentes variables y métodos:
			#   b2b_fields_to_watch <type 'tuple'>
			#   b2b_is_notifiable <type 'function'>
			#   b2b_get_data <type 'function'>
			exec(self.code, locals())
			# Devuelve False si ninguno de los campos recibidos en vals
			# está presente en b2b_fields_to_watch (cuando los tipos coinciden)
			if type(b2b_fields_to_watch) is tuple and type(vals) is dict:
				vals_set = set(vals)
				fields_set = set(b2b_fields_to_watch)
				is_notifiable = bool(vals_set.intersection(fields_set))
			# Comprobamos si se debe notificar según el código
			if is_notifiable and b2b_is_notifiable(record, vals):
				return b2b_get_data(record)
			return False
		return False

	@api.one
	def sync_item(self, mode='create'):
		"""
		Sync all model records
		"""
		search_query = [] # Default query
		record_number = 0.0 # Record counter
		docs_min_date = '2019-01-01' # Begin date

		# Acelerate certain models
		# with specific queries
		if self.model == 'product.product':
			search_query = ['&', ('type', '=', 'product'), ('tag_ids', '!=', False)]
		elif self.model == 'product.template':
			search_query = ['&', '&', ('type', '=', 'product'), ('tag_ids', '!=', False), ('product_attribute_count', '>', 0)]
		elif self.model == 'stock.move':
			search_query = ['&', '&', '&', ('state', 'in', ['assigned', 'done', 'cancel']), ('company_id', '=', 1), ('purchase_line_id', '!=', False), ('date_expected', '>=', str(datetime.now().date()))]
		elif self.model == 'res.partner':
			search_query = ['|', ('type', '=', 'delivery'), ('is_company', '=', True)]
		elif self.model == 'account.invoice':
			search_query = [('date_invoice', '>=', docs_min_date)]
		elif self.model == 'stock.picking':
			search_query = [('date_done', '>=', docs_min_date)]
		elif self.model == 'sale.order':
			search_query = [('date_order', '>=', docs_min_date)]

		# Get code model records
		records_ids = self.env[self.model].search(search_query, order='id ASC').ids
		total_records =  len(records_ids)
		print("*************** B2B ITEM ***************")
		print("@@ ITEM NAME", str(self.name))
		print("@@ ITEM MODEL", str(self.model))
		print("@@ TOTAL RECORDS", total_records)
		for id in records_ids:
			record_number += 1
			record_percent = round((record_number / total_records) * 100, 1)
			record_percent_str = str(record_percent) + '%'
			record = self.env[self.model].browse(id)
			# Exec code
			item_data = self.must_notify(record)
			if item_data:
				print("@@ RECORD ID#%s IS NOTIFIABLE!" % (record.id), record_percent_str)
				# Make & send packet
				packet = JSync(record.id)
				packet.name = self.name
				packet.data = item_data
				packet.filter_data()
				packet.send(action=mode)
			else:
				print("@@ RECORD ID#%s NOT NOTIFIABLE" % (record.id), record_percent_str)
		# End line
		print("************* FIN B2B ITEM *************")

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		"""
		Check model % code on create
		"""
		item = super(B2bItems, self).create(vals)
		item.__check_model()
		item.__check_code()
		return item

	@api.multi
	def write(self, vals):
		"""
		Check model % code on write
		"""
		super(B2bItems, self).write(vals)
		for item in self:
			item.__check_model()
			item.__check_code()
		return True
