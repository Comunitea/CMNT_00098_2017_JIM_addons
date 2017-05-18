# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    purchase_ids = fields.Many2many('purchase.order', compute='_compute_purchase_ids',
                                   string='Purchases associated to this sale')
    purchase_count = fields.Integer(string='Purchases', compute='_compute_purchase_ids')

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.mapped('purchase_ids'):
            ic_purchases = self.purchase_ids.filtered(lambda x: x.intercompany)
            ic_purchases.button_confirm()

        return res


    @api.multi
    @api.depends('procurement_group_id')
    def _compute_purchase_ids(self):
        for order in self:
            order.purchase_ids = self.env['purchase.order'].search(
                [('group_id', '=', order.procurement_group_id.id)]) if order.procurement_group_id else []
            order.purchase_count = len(order.purchase_ids)

    @api.multi
    def action_view_purchase(self):
        '''
        This function returns an action that display existing purchase orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one purchase order to show.
        '''
        action = self.env.ref('purchase.purchase_form_action').read()[0]

        purchases = self.mapped('purchase_ids')
        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif purchases:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchases.id
        return action