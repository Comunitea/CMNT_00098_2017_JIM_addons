# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import ormcache
import requests as request

PARAMS = {
	'url': ('b2b.server_url', 'http://0.0.0.0/'),
	'conexion_error': ('b2b.show_conexion_error', True),
	'response_error': ('b2b.show_response_error', True),
	'server': ('b2b.ftp_server', 'premium17.web-hosting.com'),
	'base_url': ('b2b.public_base_url', 'https://jimsports.website/b2b_images/'),
	'user': ('b2b.ftp_user', False),
	'password': ('b2b.ftp_password', False),
	'docs_after': ('b2b.docs_min_date', '2020-01-01')
}

class B2BSettings(models.TransientModel):
	_name = 'b2b.settings'
	_inherit = 'res.config.settings'

	url = fields.Char('JSync URL', required=True, translate=False, help="Set the server URL (http://ip:port/)")
	conexion_error = fields.Boolean('Conexion errors', help="Disturb user with conexion errors and do not execute the action")
	response_error = fields.Boolean('Response errors', help="Disturb user with response errors and do not execute the action")
	base_url = fields.Char('Public Base URL', required=False, translate=False, help="Images public base URL")
	server = fields.Char('Public Server', required=False, translate=False, help="Set the server IP or domain")
	user = fields.Char('User', required=False, translate=False, help="Set the FTP server username")
	password = fields.Char('Password', required=False, translate=False, help="Set the TP server password")
	docs_after = fields.Datetime('Min Date')

	@staticmethod
	def _url_check(url):
		# Check if URL starts with http
		if not (url.startswith('http://') or url.startswith('https://')):
			raise ValidationError('B2B Settings Error\nThe server address must be a valid URL')
		# Check if URL ends with /
		if not url.endswith('/'):
			url += '/'
		return url

	@api.multi
	def execute(self):
		# Check JSync URL
		if getattr(self, 'url', False):
			self.url = B2BSettings._url_check(self.url)
			# Reset HTTPClient session
			b2b_session = request.session()
			b2b_session.close()
		# Check public URL
		if getattr(self, 'base_url', False):
			self.base_url = B2BSettings._url_check(self.base_url)
		return super(B2BSettings, self).execute()

	@api.model
	@ormcache('param')
	def get_param(self, param, value=None):
		if param in PARAMS:
			key_name = PARAMS[param][0]
			default_val = PARAMS[param][1]
			return safe_eval(self.env['ir.config_parameter'].sudo().get_param(key_name, repr(default_val)))
		return False

	@api.model
	def update_param(self, param, value=None):
		if param in PARAMS:
			key_name = PARAMS[param][0]
			default_val = PARAMS[param][1]
			self.env['ir.config_parameter'].set_param(key_name, repr(value or default_val))
			#self.get_param.clear_cache(self.filtered(lambda r: r.key == 'param'))
			self.clear_caches()
		return True

	@api.multi
	def set_params(self):
		self.ensure_one()
		for field_name, field_attrs in PARAMS.items():
			key_name = field_attrs[0]
			default_val = field_attrs[1]
			value = repr(getattr(self, field_name, default_val))
			self.env['ir.config_parameter'].set_param(key_name, value)
			#self.get_default_params.clear_cache(self.filtered(lambda r: r.key == 'fields'))
			self.clear_caches()
		return True

	@api.model
	@ormcache('fields')
	def get_default_params(self, vals=[], fields=PARAMS.keys()):
		res = dict()
		for field_name in fields:
			key_name = PARAMS[field_name][0]
			default_val = PARAMS[field_name][1]
			res[field_name] = safe_eval(self.env['ir.config_parameter'].sudo().get_param(key_name, repr(default_val)))
		return res