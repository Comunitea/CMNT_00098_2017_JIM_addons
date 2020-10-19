# -*- coding: utf-8 -*-
from odoo import models, fields, api

class GoToProductWizard(models.TransientModel):
    _name = 'gotoproduct.wizard'

    def _restrict_product_variants(self):
        variants = self.env['product.template'].browse(self.env.context.get('default_product_id')).product_variant_ids
        return [('id', 'in', variants._ids)]

    product_variant = fields.Many2one('product.product', string='Product Variant', domain=_restrict_product_variants)

    @api.multi
    def go_to_variant(self):
        return self.product_variant.parameterization_modal()