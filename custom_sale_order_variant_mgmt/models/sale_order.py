# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrderLineTemplate(models.Model):

    _name = 'sale.order.line.template'
    _inherit = 'sale.order.line'

    product_template = fields.Many2one(
        'product.template', string='Product',
        domain=[('sale_ok', '=', True), ('product_variant_count', '=', 1)],
        change_default=True, ondelete='restrict', required=True)

    order_lines = fields.One2many('sale.order.line', 'template_line')
    lines_qty = fields.Integer(compute='_compute_order_lines_qty')
    price_subtotal = fields.Monetary(
        compute='_compute_amount', string='Subtotal', readonly=True, store=True)

    @api.depends('order_lines.price_subtotal')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = sum([x.price_subtotal for x in line.order_lines])

    @api.multi
    def unlink(self):
        for tempalte in self:
            tempalte.order_lines.unlink()
        return super(SaleOrderLineTemplate,self).unlink()

    @api.multi
    def write(self, vals):
        for template in self:
            line_vals = vals
            if template.lines_qty > 1:
                line_vals.pop('product_id', False)
                line_vals.pop('product_uom_qty', False)
                line_vals.pop('price_unit', False)
                line_vals.pop('purchase_price', False)
                line_vals.pop('name', False)
            template.order_lines.write(vals)
        return super(SaleOrderLineTemplate, self).write(vals)

    @api.model
    def create(self, vals):
        if not self._context.get('no_create_line', False):
            new_line = self.env['sale.order.line'].create(vals)
            vals['order_lines'] = [(6, 0, [new_line.id])]
        return super(SaleOrderLineTemplate, self).create(vals)

    def _compute_order_lines_qty(self):
        for template in self:
            template.lines_qty = len(template.order_lines)

    @api.onchange('product_template')
    def onchange_template(self):
        if not self.product_template:
            return
        self.product_id = self.product_template.product_variant_ids[0]


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    template_line = fields.Many2one('sale.order.line.template')

    @api.model
    def create(self, vals):
        if self._context.get('template_line', False):
            vals['template_line'] = self._context.get('template_line', False)
        return super(SaleOrderLine, self).create(vals)


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    template_lines = fields.One2many('sale.order.line.template', 'order_id')
    sale_order_line_count = fields.Integer(compute='_compute_sale_order_line_count')

    @api.depends('order_line')
    def _compute_sale_order_line_count(self):
        for order in self:
            order.sale_order_line_count = len(order.order_line)

    @api.multi
    def action_view_order_lines(self):
        action = self.env.ref('custom_sale_order_variant_mgmt.sale_order_line_action').read()[0]
        action['domain'] = [('id', 'in', self.order_line.ids)]
        return action
