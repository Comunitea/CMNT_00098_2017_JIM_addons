# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    web_vip_client = fields.Boolean('Web Client', company_dependent=True, default=False, help="Send this client account to VIP web portals")