# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _



class SaleOrder(models.Model):
    _inherit = "sale.order"

    claim_id = fields.Many2one("crm.claim", "RMA")
