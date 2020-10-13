# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResUsers(models.Model):
	_inherit = 'res.users'

	print_pdf_last_page = fields.Boolean('PDF Last Page', default=True, help="Desactiva esta casilla para no ver las últimas páginas, tus PDF se generarán todos al vuelo")