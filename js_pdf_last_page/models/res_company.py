# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResCompany(models.Model):

    _inherit = 'res.company'

    pdf_last_pages = fields.One2many('reports.last_page', 'company_id', string="Last Pages")