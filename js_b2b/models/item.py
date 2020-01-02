# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..base.helper import JSync
import re

class B2bItems(models.Model):
	_name = 'b2b.item'
	_description = "B2B Item"

	_default_code_str = re.sub(r'(^[ ]{0,8})', '', """
		# Fields to watch
		# Tuple of fields
		fields_to_watch = None

		# When this model is notifiable
		# Returns True or False
		def is_notifiable(self):
			return self._name == 'res.partner'

		# Recipients of data
		# Odoo partner references list
		def send_to(self):
			return []

		# Get model data for a item
		# Object data dictionary
		def get_data(self):
			return { }
	""", flags=re.M).strip()

	name = fields.Char('Item Name', required=False, translate=False, help="Set the item name")
	partners = fields.Many2many('res.partner', 'b2b_item_partner_rel', string='Partners')
	code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
	premium = fields.Boolean('Premium', default=False, help="Is a premium item")
	active = fields.Boolean('Active', default=True, help="Enable or disable this item")

	@staticmethod
	def __check_code(code):
		if type(code) is unicode:
			# Exec B2B Item Code
			try:
				exec(code)
			except Exception as e:
				raise UserError(_('Syntax Error!\n') + str(e))
			# Check required vars and methods to avoid errors
			variables = { 'fields_to_watch': tuple }
			methods = ['is_notifiable', 'send_to', 'get_data']
			for var in tuple(variables.keys() + methods):
				if not var in locals():
					raise UserError(_('Code Error!\n %s not defined' % (var)))
			for var, typ in variables.items():
				if type(eval(var)) is not typ:
					raise UserError(_('Code Error!\n %s must be a %s' % (var, typ)))
			for method in methods:
				if not callable(eval(method)):
					raise UserError(_('Code Error!\n %s must be a function' % (method)))

	def __b2b_record(self, mode='create', vals=None):  
		jitem = JSync()
		# Set data
		jitem.obj_id = self.id
		jitem.obj_type = 'item'
		jitem.obj_data = { 
			'name': self.name, 
			'premium': self.premium
		}
		# Filter data
		jitem.filter_obj_data(vals)
		# Send item
		jitem.send('config', mode, 60)

	# -------------------------------------------------------------------------------------------
	@api.multi
	def toggle_premium(self):
		for item in self:
			item.premium = not item.premium

	@api.model
	def create(self, vals):
		self.__check_code(vals.get('code'))
		item = super(B2bItems, self).create(vals)
		item.__b2b_record('create', vals)
		return item

	@api.multi
	def write(self, vals):
		self.__check_code(vals.get('code'))
		super(B2bItems, self).write(vals)
		for item in self:
		   item.__b2b_record('update', vals)
		return True

	@api.multi
	def unlink(self):
		for item in self:
			item.__b2b_record('delete')
		super(B2bItems, self).unlink()
		return True