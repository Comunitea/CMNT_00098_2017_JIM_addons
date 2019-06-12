# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    general_category = fields.Selection(['GENERAL', 'COMPLEMENTO DEPORTIVO'], 'General Category')

# class ProductProduct(models.Model):
    # _inherit = "product.product"

#
    # discontinued_product = fields.Boolean('Discontinued', default=False, help="If checked, the variant will not be sold in main company")
