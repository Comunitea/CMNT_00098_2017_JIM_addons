# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.one
    @api.depends('attribute_line_ids')
    def _compute_product_attribute_count(self):
        self.product_attribute_count = len(self.attribute_line_ids)


    product_attribute_count = fields.Integer('# Product Attribute', compute='_compute_product_attribute_count', store=True)