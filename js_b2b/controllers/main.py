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
	], type='json', auth='public', methods=['POST',])
	def message(self, **kw):
		env = http.request.env
		
		try:
			# Process message
			data_obj = http.request.params
			item_user = data_obj.get('user_id', 0)
			item_company = data_obj.get('user_company', 0)
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

			# Check client company or client
			has_company = item_company and self.env['res.company'].browse(item_company).mapped('partner_id') == item_user
			has_partner = not has_company and item_user and self.env['res.partner'].browse(item_user)

			# Is company or client
			if has_company or has_partner:

				# Process item
				if env['b2b.item.in'].sudo().must_process(item_name, item_data, item_action):
					# OK
					_logger.info(debug_str)
				else:
					# ERROR
					_logger.error(debug_str)

			else:
				# Invalid user
				_logger.critical('User with ID %s and company ID %s not allowed' % (item_user, item_company))	

		except ValueError:
			# Invalid JSON
			_logger.warning("Invalid JSON received: %s" % message.data)