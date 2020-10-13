# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsers(models.Model):
	_inherit = 'res.users'

	show_b2b_notifications = fields.Boolean('B2B Notifications', default=False, help="Habilita las notificaciones de registros para el módulo B2B")