# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
import requests as request

PARAMS = {
	'url': ('b2b.server_url', 'http://0.0.0.0/'),
	'conexion_error': ('b2b.show_conexion_error', True),
	'response_error': ('b2b.show_response_error', True),
	'packet_size': ('b2b.packet_size_mb', 10),
	'server': ('b2b.ftp_server', 'premium17.web-hosting.com'),
	'user': ('b2b.ftp_user', False),
	'password': ('b2b.ftp_password', False)
}

class B2BSettings(models.TransientModel):
	_name = 'b2b.settings'
	_inherit = 'base.config.settings'

	url = fields.Char('JSync URL', required=True, translate=False, help="Set the server URL (http://ip:port/)")
	conexion_error = fields.Boolean('Conexion errors', help="Disturb user with conexion errors and do not execute the action")
	response_error = fields.Boolean('Response errors', help="Disturb user with response errors and do not execute the action")
	packet_size = fields.Float(string='Max. Packet Size', help="Messages that exceeds this limit are splited")
	server = fields.Char('Public Server', required=False, translate=False, help="Set the server IP or domain")
	user = fields.Char('User', required=False, translate=False, help="Set the FTP server username")
	password = fields.Char('Password', required=False, translate=False, help="Set the TP server password")

	@api.multi
	def execute(self):
		if getattr(self, 'url', False):
			# Check if URL starts with http
			if not (self.url.startswith('http://') or self.url.startswith('https://')):
				raise ValidationError('B2B Settings Error\nThe server address must be a valid URL')
			# Check if URL ends with /
			if not self.url.endswith('/'):
				self.url += '/'
			# Reset HTTPClient session
			b2b_session = request.session()
			b2b_session.close()
		return super(B2BSettings, self).execute()

	@api.model
	def update_param(self, param, value=None):
		if param in PARAMS:
			key_name = PARAMS[param][0]
			default_val = PARAMS[param][1]
			self.env['ir.config_parameter'].set_param(key_name, repr(value or default_val))

	@api.multi
	def set_params(self):
		self.ensure_one()
		for field_name, field_attrs in PARAMS.items():
			key_name = field_attrs[0]
			default_val = field_attrs[1]
			value = repr(getattr(self, field_name, default_val))
			self.env['ir.config_parameter'].set_param(key_name, value)

	@api.model
	def get_default_params(self, vals=[], fields=PARAMS.keys()):
		res = dict()
		for field_name in fields:
			key_name = PARAMS[field_name][0]
			default_val = PARAMS[field_name][1]
			res[field_name] = safe_eval(self.env['ir.config_parameter'].sudo().get_param(key_name, repr(default_val)))
		return res