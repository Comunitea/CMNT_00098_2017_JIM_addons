# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger('B2B-IN')

# ERRORS #############################
# 600 Item don't exists or is archived
# 610 CRUD mode don't exists
# 620 Item configuration error
# 630 Data error

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
	def __change_active_company(self, company_id):

		"""
		Change company
		"""

		if company_id not in self.env.user.company_ids.ids:
			_logger.info('[400] User not authorized on company %s' % company_id)
			return False
		# Change current company (mandatory)
		self.env.user.company_id = company_id
		return True

	@api.model
	def evaluate(self, **kwargs):

		"""
		Evaluate config code
		"""

		b2b = dict()
		# Introducimos el logger
		b2b['logger'] = _logger
		# Actualizamos con kwargs
		if kwargs: b2b.update(kwargs)
		# Librerías permitidas en el código
		from datetime import datetime
		# Ejecutamos el código con exec(item.code)
		exec(self.code, locals(), b2b)
		# Devolvemos la variable b2b
		return b2b

	@api.model
	def must_process(self, object_name, data, mode='create'):

		"""
		Check if item record is configured and do operation
		"""

		# Data check
		if data and type(data) is dict:

			# Change current company (mandatory)
			company_id = data.get('company_id', 1)
			if not self.__change_active_company(company_id):
				return False
				
			# Process item based on config
			item = self.search([('name', '=', object_name), ('active', '=', True)], limit=1)

			if item and type(item.code) is unicode:

				# Configuration eval
				b2b = item.evaluate()

				if mode in ('create', 'update', 'cancel'):

					# Ejecutamos la función pre_data si existe
					if 'pre_data' in b2b and callable(b2b['pre_data']):
						b2b['pre_data'](self, mode)

					item_data = b2b['get_data'](self, data)
					item_action = b2b['get_action'](mode, data)
					# Comprobaciones de seguridad
					item_data_ok = type(item_data) is dict
					item_action = getattr(self.env[item.model], item_action, None)

					if item_data and item_data_ok and callable(item_action):

						# Ejecutamos la acción del mensaje
						try:
							record_id = item_action(item_data)

							# Ejecutamos la función pos_data si existe
							if record_id and 'pos_data' in b2b and callable(b2b['pos_data']):
								record = self.env[item.model].browse(record_id)
								b2b['pos_data'](record, mode)

							if record_id:
								return True

						except Exception as e:
							return '[630] Can not create the record! %s' % e

					else:
						return '[620] Item %s configuration or data error!' % object_name

				else:
					return '[610] CRUD mode %s not found for item %s!' % (item_action, object_name)

			else:
				return '[600] Item %s not found!' % object_name

		return '[500] Data format error!'

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

		self.invalidate_cache()
		super(B2bItemsIn, self).write(vals)
		for item in self:
			item.__check_model()
			item.__check_code()
		return True