# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..base.helper import JSync
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

        # Object data to send
        def get_data(self, action):
            return {
                # Item key (required)
                # fixed: modifier forces send even if it has not changed
                'fixed:jim_id': self.id,
                # Sends names dict when field has changed
                'name': self.get_field_translations('name'),
                # field: modifier sends if field has changed, if not setted send null
                'categ_id:category_id': self.categ_id.id if self.categ_id else None,
                # upload: modifier uploads base64 image to public server and replaces this param with the URL
                'upload:logo': '/9j/4AAQSkZJRgABAQAAAQABAAD...'
            }
	""", flags=re.M).strip()

	name = fields.Char('Item Name', required=True, translate=False, help="Set the item name")
	model = fields.Char('Model Names', required=True, translate=False, help="Odoo model names to check separated by , or ;")
	description = fields.Char('Description', required=False, translate=False, help="Set the item description")
	code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
	active = fields.Boolean('Active', default=True, help="Enable or disable this item")
	sequence = fields.Integer(help="Determine the items order")

	@api.model
	def __check_model(self):
		"""
		Check if is a valid model
		"""
		separators = (',', ';')

		for separator in separators:
			if separator in self.model:
				for model in self.model.split(separator):
					model_name = model.strip()
					
					try:
						self.env[model_name].search_count([])
					except Exception as e:
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
			notifiable_items = record.is_notifiable_check()
			# Is notifiable
			if notifiable_items:
				print("@@ RECORD ID#%s IS NOTIFIABLE!" % (id), record_percent_str)
				record.b2b_record('create', conf_items_before=notifiable_items)
			else:
				print("@@ RECORD ID#%s NOT NOTIFIABLE" % (id), record_percent_str)
		# End line
		print("************* FIN B2B ITEM *************")

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
		super(B2bItemsOut, self).write(vals)
		for item in self:
			item.__check_model()
			item.__check_code()
		return True