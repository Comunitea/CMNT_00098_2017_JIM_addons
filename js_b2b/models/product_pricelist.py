# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ProductPricelist(models.Model):

    _inherit = 'product.pricelist'

    web = fields.Boolean('Web', help="Export this pricelist for web")