# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..base.helper import JSync
import re

class B2bItemsIn(models.Model):
	_name = 'b2b.item.in'
	_description = 'B2B Item In'
	_order = 'sequence, id'
	_sql_constraints = [('b2b_item_in_unique', 'unique(name)', 'Name must be unique into B2B Incoming Items!')]

	_default_code_str = re.sub(r'(^[ ]{0,8})', '', """
        # Model method to call
        def get_action(action, data):
            return action

        # Object data to create
        def get_data(data):
            return {
                # Odoo record data
                'name': self.name
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
		methods = tuple(['get_action', 'get_data'])
		for var in methods:
			if not var in locals():
				raise UserError(_('Code Error!\n %s not defined' % (var)))
		for method in methods:
			if not callable(eval(method)):
				raise UserError(_('Code Error!\n %s must be a function' % (method)))

	@api.model
	def must_process(self, object_name, partner_id, data, action='create'):
		"""
		Check if item record its configured and do save operation
		"""
		# Data check
		if data and type(data) is dict:
			# Check if client exists
			if self.env['res.partner'].browse(partner_id):
				# Process item based on config
				item_conf = self.search([('name', 'like', object_name), ('active', '=', True)], limit=1)
				if item_conf and type(item_conf.code) is unicode:
					b2b = dict()

					# Ejecutamos el código con exec(item_conf.code)
					# establece localmente las siguentes variables y métodos:
					#	b2b['get_action'] <type 'function'>
					#   b2b['get_data'] <type 'function'>
					exec(item_conf.code, locals(), b2b)

					# Obtener la acción a realizar con los datos
					action = b2b['get_action'](action, data)
					if action:
						# Comprobaciones de seguridad
						item_data = b2b['get_data'](self, data)
						item_data_ok = type(item_data) is dict
						incoming_user = self.env['res.users'].browse(188) # Prestadoo
						item_model = self.env[item_conf.model].sudo(incoming_user)
						item_action = getattr(item_model, action, None)
						item_action_ok = action in ('create', 'update', 'cancel')
						if item_data and item_data_ok and callable(item_action) and item_action_ok:
							item_action(item_data)
							return True
		return False

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		"""
		Check model on create
		"""
		item = super(B2bItemsIn, self).create(vals)
		item.__check_model()
		item.__check_code()
		return item

	@api.multi
	def write(self, vals):
		"""
		Check model on write
		"""
		super(B2bItemsIn, self).write(vals)
		for item in self:
			item.__check_model()
			item.__check_code()
		return True