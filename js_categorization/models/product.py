# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

GENERAL_CATEGORY_VALUES = [
    ('draft', 'Draft'),
    ('confirmed', 'confirmed'),
    ('done', 'Done')
]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # self.env['ir.config_parameter'].get_param('js_categorization.general_categories')

    general_category = fields.Selection(GENERAL_CATEGORY_VALUES, 'General Category')

# class ProductProduct(models.Model):
    # _inherit = "product.product"

#
    # discontinued_product = fields.Boolean('Discontinued', default=False, help="If checked, the variant will not be sold in main company")
