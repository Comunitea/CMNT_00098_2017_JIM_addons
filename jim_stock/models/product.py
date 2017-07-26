# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api
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

    @api.multi
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

    @api.multi
    def _get_web_stock(self):
        for product in self:
            stock = product.global_real_stock
            if product.bom_count:
                for bom in product.bom_ids:
                    min_qty = 0
                    for line in bom.bom_line_ids:
                        qty = line.product_id.global_available_stock / \
                            line.product_qty
                        if qty < min_qty:
                            min_qty = qty
                    if min_qty < 0:
                        min_qty = 0
                    stock += (min_qty * bom.product_qty)
            else:
                bom_lines = self.env["mrp.bom.line"].\
                    search([('product_id', '=', product.id)])
                for line in bom_lines:
                    if line.product_qty:
                        stock += \
                            line.bom_id.product_tmpl_id.\
                            global_available_stock * line.product_qty
            product.web_global_stock = stock

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
    web_global_stock = fields.Float('Web stock', readonly=True,
                                    digits=dp.get_precision
                                    ('Product Unit of Measure'),
                                    compute="_get_web_stock")

    @api.multi
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
