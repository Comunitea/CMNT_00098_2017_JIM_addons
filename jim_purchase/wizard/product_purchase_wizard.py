# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api,_
from openerp.exceptions import ValidationError

class ProductPurchaseLineWizard(models.TransientModel):
    _name = "product.purchase.line.wizard"

    product_id = fields.Many2one('product.product')
    product_qty = fields.Float("Quantity", default=0.00)
    product_purchase_wzd_id = fields.Many2one('product.purchase.wizard')

class ProductPurchaseWizard(models.TransientModel):

    _name = "product.purchase.wizard"

    purchase_order = fields.Many2one('purchase.order')
    line_ids = fields.One2many('product.purchase.line.wizard', 'product_purchase_wzd_id')

    def add_to_purchase_order(self):

        if not self.purchase_order:
            raise ValidationError(_("No order selected"))
        OrderLine = self.env['purchase.order.line']
        ids = [x.product_id.id for x in self.line_ids]
        domain = [('order_id', '=', self.purchase_order.id), ('product_id','in', ids)]
        lines_to_unlink = self.env['purchase.order.line'].search(domain)
        lines_to_unlink.unlink()

        for line in self.line_ids:
            order_line = OrderLine.new({
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id,
                'order_id': self.purchase_order.id,
                'product_qty': line.product_qty})
            order_line.onchange_product_id()
            order_line.product_qty = line.product_qty
            order_line_vals = order_line._convert_to_write(
                order_line._cache)
            self.purchase_order.order_line.create(order_line_vals)

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'res_id': self.purchase_order.id,
            'context': self.env.context
        }


    @api.model
    def default_get(self, fields):
        res = super(ProductPurchaseWizard, self).default_get(fields)
        product_ids = self.env.context.get('active_ids', [])
        lines = []
        if not product_ids:
            return res
        for product in product_ids:
            lines.append({'product_id': product, 'product_qty': 0})

        res['line_ids'] = map(lambda x: (0,0,x), lines)

        return res
