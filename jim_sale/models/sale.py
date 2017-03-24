# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('lqdr', 'LQDR'),
        ('pending', 'Pending Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    @api.multi
    def action_lqdr_pending(self):
        for order in self:
            if order.order_line.filtered('product_id.lqdr'):
                order.state = 'lqdr'
            else:
                order.state = 'pending'
        return True

    @api.multi
    def action_pending(self):
        for order in self:
            order.state = 'pending'
        return True


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

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id.route_ids:
            self.route_id = self.product_id.route_ids[0]
        return res

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """
        Avoid change warehouse_company_id
        """
        return
