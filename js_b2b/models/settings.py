# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class B2BSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    b2b_conexion_error = fields.Boolean('Conexion errors', default=True, help="Disturb user with conexion errors and do not execute the action.")
    b2b_response_error = fields.Boolean('Response errors', default=True, help="Disturb user with response errors and do not execute the action.")

    @api.multi
    def set_b2b_conexion_error(self):
        return self.env['ir.values'].sudo().set_default('base.config.settings', 'b2b_conexion_error', self.b2b_conexion_error)

    @api.multi
    def set_b2b_response_error(self):    
        return self.env['ir.values'].sudo().set_default('base.config.settings', 'b2b_response_error', self.b2b_conexion_error and self.b2b_response_error)