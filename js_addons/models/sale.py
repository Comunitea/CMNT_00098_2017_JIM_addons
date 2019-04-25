# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Si una de las variantes está descatalogada decimos que la plantilla también lo está
    def _template_discontinued(self):
        if hasattr(self, 'order_lines'):
            for line in self.order_lines:
                if (line.product_id.discontinued_product):
                    return True

        if hasattr(self, 'product_id') and hasattr(self.product_id, 'discontinued_product'):
            return self.product_id.discontinued_product

        return False

    # discontinued_product = fields.Boolean('Discontinued', default=False, related='product_id.discontinued_product')
    discontinued_line = fields.Boolean(compute='_compute_product_discontinued')

    @api.depends('product_id')
    def _compute_product_discontinued(self):
        for record in self:
            record.discontinued_line = record._template_discontinued()

    @api.model
    def ts_product_id_change(self, product_id, partner_id, pricelist_id, get_stock=True):
        product = self.env['product.product'].browse(product_id)
        result = super(SaleOrderLine, self).ts_product_id_change(product_id, partner_id, pricelist_id)

        result.update({
            'discontinued': product.discontinued_product
        })

        return result
