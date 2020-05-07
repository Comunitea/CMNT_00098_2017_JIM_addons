# -*- coding: utf-8 -*-
# © 2020 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _


class ExportCustomerPrices(models.Model):

    _name = 'export.customer.prices'

    product_id = fields.Many2one('product.product', 'Product')
    partner_id = fields.Many2one('res.partner', 'Pricelist')
    price = fields.Float('Price')
    last_sinc = fields.Datetime('Last sync')
