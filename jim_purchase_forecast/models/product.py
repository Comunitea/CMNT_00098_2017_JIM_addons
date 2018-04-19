# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api


class PurchaseForecast(models.Model):

    _inherit = "product.product"

    demand = fields.Float('Demand')
    purchase = fields.Float('Recommended purchase')

    @api.multi
    def get_purchase_forecast(self):
        self.write({'demand': 69, 'purchase': 10069})
