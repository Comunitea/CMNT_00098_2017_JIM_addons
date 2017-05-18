# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('lqdr', 'Pending LQDR'),
        ('progress_lqdr', 'Progress LQDR'),
        ('pending', 'Pending Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    @api.multi
    def action_lqdr_option(self):
        for order in self:
            if order.order_line.filtered('product_id.lqdr'):
                order.state = 'lqdr'
            else:
                order.action_confirm()
                order.action_sale()
        return True

    @api.multi
    def action_progress_lqdr(self):
        for order in self:
            order.action_confirm()
            order.state = 'progress_lqdr'
        return True

    @api.multi
    def action_lqdr_done(self):
        for order in self:
            order.action_sale()
        return True

    @api.multi
    def action_sale(self):
        for order in self:
            order.state = 'sale'
            picking_out = order.picking_ids.filtered(lambda x: x.picking_type_id.code == 'outgoing')
            picking_out.ready = True
        return True

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """
        Avoid change warehouse_company_id
        """
        return


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
        if self.product_id.route_ids:
            self.route_id = self.product_id.route_ids[0]
        return res
