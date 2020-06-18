# -*- coding: utf-8 -*-
from odoo import http
import logging
import json

_logger = logging.getLogger(__name__)

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
	], type='json', auth='public', methods=['POST',])
	def message(self, **kw):
		env = http.request.env
		
		try:
			# Process message
			data_obj = http.request.params
			item_user = data_obj.get('user_id')
			item_name = data_obj.get('object')
			item_action = data_obj.get('action', 'create')
			item_data = data_obj.get('data')

			# Debug data
			debug_str = "[B2B INCOMING] Message: " \
					"\n    - name: {}" \
					"\n    - user: {}" \
					"\n    - operation: {}" \
					"\n    - data: {}".format(item_name, item_user, item_action, item_data)

			# Process item
			if env['b2b.item.in'].sudo().must_process(item_name, item_user, item_data, item_action):
				# OK
				_logger.info(debug_str)
			else:
				# ERROR
				_logger.error(debug_str)

		except ValueError:
			# Invalid JSON
			_logger.warning("[PUBLIC-IN] Invalid JSON received: %s" % message.data)