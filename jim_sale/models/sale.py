# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
import time
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('proforma', 'Proforma'),
        ('lqdr', 'Pending LQDR'),
        ('progress_lqdr', 'Progress LQDR'),
        ('pending', 'Revision Pending '),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    work_to_do = fields.Text('Trabajo a realizar')
    route_id = fields.Many2one('stock.location.route', string='Force Route', domain=[('sale_selectable', '=', True)])

    @api.multi
    def action_proforma(self):
        for order in self:
            order.state = 'proforma'
        return True

    @api.multi
    def action_lqdr_option(self):
        for order in self:
            if order.order_line.filtered('product_id.lqdr'):
                order.state = 'lqdr'
            else:
               order.state = 'pending'
        return True

    @api.multi
    def action_lqdr_ok(self):
        for order in self:
            order.state = 'pending'
        return True

    @api.multi
    def action_pending_ok(self):
        for order in self:
            order.action_sale()
        return True

    @api.multi
    def action_sale(self):
        for order in self:
            order.action_confirm()
            picking_out = order.picking_ids.filtered(lambda x: x.picking_type_id.code == 'outgoing')
            picking_out.write({'ready': True})
        return True

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """
        Avoid change warehouse_company_id
        """
        return


    def apply_route_to_order_lines(self):

        for order in self:
            if order.state == 'done':
                raise ValueError ("No puedes asignar rutas a un pedido confirmado")
            for line in order.template_lines:
                line.route_id = order.route_id
            for line in self.order_line:
                line.route_id = self.route_id

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('lqdr', 'LQDR'),
        ('pending', 'Pending Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    lqdr = fields.Boolean(related="product_id.lqdr", store=False)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        #if self.product_id.route_ids:
        self.route_id = self.order_id.route_id or self.product_id.route_ids and self.product_id.route_ids[0]

        return res

    @api.multi
    def _get_display_price(self, product):
        res = super(SaleOrderLine, self)._get_display_price(product)
        # Search for specific prices in variants
        qty = product._context.get('quantity', 1.0)
        vals = {}
        partner_id = self.order_id.partner_id.id
        date = self.order_id.date_order
        customer_price = self.env['customer.price'].\
                    get_customer_price(partner_id, product, qty, date=date)
        if customer_price:
            return customer_price
        return res

    @api.multi
    def action_procurement_create(self):
        old_state = self.order_id.state
        self.order_id.state = 'sale'
        new_procs = self._action_procurement_create()
        self.order_id.state = old_state
        return new_procs

    @api.multi
    def _action_procurement_create(self):
        return super(SaleOrderLine, self)._action_procurement_create()


class SaleOrderLineTemplate(models.Model):

    _inherit = 'sale.order.line.template'

    lqdr = fields.Boolean(related="product_template.lqdr", store=False)

    @api.multi
    def create_template_procurements(self):
        for line in self.order_lines:
            line.action_procurement_create()
        return True
