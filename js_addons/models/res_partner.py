# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    group_companies_ids = fields.Many2many('res.company', string='Web Access')
