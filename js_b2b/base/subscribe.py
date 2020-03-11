# -*- coding: utf-8 -*-
from odoo import api, models, tools, SUPERUSER_ID
from .helper import OutputHelper, Google
from inspect import getmembers
from pprint import pprint
import json

# Suscriber class
class SubB2B(models.Model):
	"""
		Permite suscribirse a un topic desde Odoo,
		de esta forma podremos usar los métodos del
		ERP al recibir el mensaje
	"""
	_name = 'b2b.subscriptions' # Fake model
	_google = Google() # Google helper
	_auto = False # No create table

	def __init__(self, registry, cr):
		# Subscribe to topics
		self._google.receive('PUBLIC-IN', self.__process_public_in)

	def __process_public_in(self, message):
		# Environment context handler
		with api.Environment.manage():
			# DB cursor context handler
			with self.pool.cursor() as cr:
				# Get Odoo environment
				env = api.Environment(cr, SUPERUSER_ID, {})
				# Process message
				try:
					# Decode JSON
					data_obj = json.loads(message.data)
					# Debug object
					OutputHelper.print_text("[PUBLIC-IN] Message: " \
						"\n    - id: {}" \
						"\n    - name: {}" \
						"\n    - operation: {}" \
						"\n    - data: {}".format(data_obj.get('id'), data_obj.get('name'), data_obj.get('object'), data_obj.get('data')), OutputHelper.INFO)
					# Get items configured
					items_in = env['b2b.item.in'].search([('name', '=', data_obj.get('object')), ('active', '=', True)])
					# If items found & data in data_obj
					if items_in and data_obj.get('data'):
						# Loop items (normally only one)
						for item in items_in:
							# Item model
							item_model = env['b2b.item.in']
							# Create item in model
							if item_model and item_model.create(data_obj['data']):
								# Acknowlege
								message.ack()
				except:
					# Invalid JSON, drop it
					message.drop()
				finally:
					# Save data
					cr.commit()