# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    vip_web_access = fields.Many2many('res.company', 'res_partner_res_company_rel', string='VIP Webs Access')