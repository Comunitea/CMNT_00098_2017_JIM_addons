# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import jwt

PULSAR_ADMIN_KEY = 'mvwDROGfNfHfFv2v/7Q9CG3qv8Fbc+rzweJQaUgciWs='

class B2bClients(models.Model):
    _name = 'b2b.client'
    _description = "B2B Client"

    partner = fields.Many2one('res.partner', 'Odoo Client', ondelete='cascade', required=True, help="Select a client")
    name = fields.Char('Client Name', required=False, translate=False, help="Client name")
    key = fields.Char('Auth. Key', required=False, translate=False, help="Authorization hash key")
    active = fields.Boolean('Active', default=True, help="Enable or disable this client")
    items = fields.Many2many('b2b.item', 'b2b_client_item_rel', string='Data Items')

    @api.onchange('name')
    def _generate_client_token(self):
        for record in self:
            record.key = jwt.encode({'sub': self.name}, PULSAR_ADMIN_KEY, algorithm='HS256')
