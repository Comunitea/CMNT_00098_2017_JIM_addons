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