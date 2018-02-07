# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields

class ResPartnerBank(models.Model):

    _inherit = 'res.partner.bank'

    partner_id = fields.Many2one(domain=[('is_company', '=', True)])
