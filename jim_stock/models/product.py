# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    global_real_stock = fields.Float('Global Real Stock',
                                     compute='_compute_global_stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.")
    global_available_stock = fields.Float('Global Available Stock',
                                          compute='_compute_global_stock',
                                          digits=dp.get_precision
                                          ('Product Unit of Measure'),
                                          help="Real stock minus outgoing "
                                          " in all companies.")

    def _compute_global_stock(self):
        global_real_stock = 0.0
        global_available_stock = 0.0
        for template in self:
            for p in template.product_variant_ids:
                global_real_stock += p.global_real_stock
                global_available_stock += p.global_available_stock
            template.global_real_stock = global_real_stock
            template.global_available_stock = global_available_stock


class ProductProduct(models.Model):
    _inherit = "product.product"

    global_real_stock = fields.Float('Global Real Stock',
                                     compute='_compute_global_stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.")
    global_available_stock = fields.Float('Global Available Stock',
                                          compute='_compute_global_stock',
                                          digits=dp.get_precision
                                          ('Product Unit of Measure'),
                                          help="Real stock minus outgoing "
                                          " in all companies.")

    def _compute_global_stock(self):
        global_real_stock = 0
        global_available_stock = 0
        deposit_real_stock = 0
        deposit_available_stock = 0
        ctx = self._context.copy()
        deposit_ids = \
            self.env['stock.location'].search([('deposit', '=', True)]).ids
        for product in self:
            global_real_stock = product.sudo().qty_available
            global_available_stock = product.sudo().qty_available - \
                product.sudo().outgoing_qty

            # Get stock global in deposit location to discount it
            if deposit_ids:
                ctx.update({'location': deposit_ids})
                deposit_real_stock = \
                    product.with_context(ctx).sudo().qty_available
                deposit_available_stock = \
                    product.with_context(ctx).sudo().qty_available - \
                    product.with_context(ctx).sudo().outgoing_qty

            product.global_real_stock = global_real_stock - deposit_real_stock
            product.global_available_stock = \
                global_available_stock - deposit_available_stock
