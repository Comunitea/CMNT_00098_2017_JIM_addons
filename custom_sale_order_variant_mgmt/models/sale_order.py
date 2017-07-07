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

    order_lines = fields.One2many('sale.order.line', 'template_line',
                                  copy=True)
    lines_qty = fields.Integer(compute='_compute_order_lines_qty')
    price_subtotal = fields.Monetary(
        compute='_compute_amount', string='Subtotal', readonly=True,
        store=True)
    global_available_stock = fields.\
        Float('Stock', related='product_template.global_available_stock')

    @api.depends('order_lines.price_subtotal')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = sum(
                [x.price_subtotal for x in line.order_lines])

    @api.multi
    def unlink(self):
        for tempalte in self:
            tempalte.order_lines.unlink()
        return super(SaleOrderLineTemplate, self).unlink()

    @api.multi
    def write(self, vals):
        for template in self:
            line_vals = vals.copy()
            if template.lines_qty > 1:
                line_vals.pop('product_id', False)
                line_vals.pop('price_unit', False)
                line_vals.pop('product_uom_qty', False)
                line_vals.pop('purchase_price', False)
                line_vals.pop('name', False)
            template.order_lines.write(line_vals)
        return super(SaleOrderLineTemplate, self).write(vals)

    @api.model
    def create(self, vals):
        # Se controla el create con order_lines debido que al duplicar un
        # pedido el vals de las lineas viene sin order_id
        if vals.get('order_lines', False):
            for line_vals in vals['order_lines']:
                if line_vals[0] == 0:
                    line_vals[2]['order_id'] = vals.get('order_id', False)
        if not self._context.get('no_create_line', False):
            new_line = self.env['sale.order.line'].with_context(
                no_create_template_line=True).create(vals)
            vals['order_lines'] = [(6, 0, [new_line.id])]
        return super(
            SaleOrderLineTemplate,
            self.with_context(no_create_template_line=True)).create(vals)

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
    global_available_stock = fields.Float('Stock')

    @api.model
    def create(self, vals):
        if self._context.get('template_line', False):
            vals['template_line'] = self._context.get('template_line', False)
        if not vals.get('template_line', False) and not \
                self._context.get('no_create_template_line', False):
            product = self.env['product.product'].browse(
                vals.get('product_id'))
            vals['product_template'] = product.product_tmpl_id.id
            new_template = self.env['sale.order.line.template'].with_context(
                no_create_template_line=True, no_create_line=True).create(vals)
            vals.pop('product_template')
            vals['template_line'] = new_template.id
        return super(SaleOrderLine, self).create(vals)


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    template_lines = fields.One2many('sale.order.line.template', 'order_id',
                                     copy=True)
    order_line = fields.One2many(copy=False)
    sale_order_line_count = fields.Integer(
        compute='_compute_sale_order_line_count')
    global_available_stock = fields.\
        Float('Stock', related='product_id.global_available_stock')

    @api.depends('order_line')
    def _compute_sale_order_line_count(self):
        for order in self:
            order.sale_order_line_count = len(order.order_line)

    @api.multi
    def action_view_order_lines(self):
        action = self.env.ref(
            'custom_sale_order_variant_mgmt.sale_order_line_action').read()[0]
        action['domain'] = [('id', 'in', self.order_line.ids)]
        return action

    @api.multi
    def copy(self, default={}):
        return super(
            SaleOrder,
            self.with_context(no_create_line=True,
                              no_create_template_line=True)).copy(default)
