# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
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

	name = fields.Char('Item Name', required=True, translate=False, help="Set the item name", index=True)
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
		if not self.model in self.env:
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
		methods = tuple(['get_action', 'get_data'])
		for var in methods:
			if not var in locals():
				raise UserError(_('Code Error!\n %s not defined' % (var)))
		for method in methods:
			if not callable(eval(method)):
				raise UserError(_('Code Error!\n %s must be a function' % (method)))

	@api.model
	def evaluate(self, mode='create', data=dict()):
		b2b = dict()
		# Librerías permitidas en el código
		from datetime import datetime
		# Ejecutamos el código con exec(item.code)
		exec(self.code, locals(), b2b)
		# Obtener la acción a realizar con los datos
		b2b['crud_mode'] = b2b['get_action'](mode, data)
		# Devolvemos la variable b2b
		return b2b

	@api.model
	def must_process(self, object_name, partner_id, company_id, data, mode='create'):
		"""
		Check if item record is configured and do operation
		"""

		# Data check
		if data and type(data) is dict:
			# Process item based on config
			item = self.search([('name', '=', object_name), ('active', '=', True)], limit=1)
			if item and type(item.code) is unicode:
				# Configuration eval
				b2b = item.evaluate(mode, data)
				b2b['partner_id'] = partner_id
				b2b['company_id'] = company_id

				if b2b['crud_mode']:
					# Comprobaciones de seguridad
					item_data = b2b['get_data'](self, data)
					item_data_ok = type(item_data) is dict
					# superuser_id = self.env['b2b.settings'].get_param('superuser')
					# incoming_user = self.env['res.users'].browse(superuser_id)
					# item_model = self.env[item.model].sudo(incoming_user)
					item_action = getattr(self.env[item.model], mode, None)
					item_action_ok = b2b['crud_mode'] in ('create', 'update', 'cancel')
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