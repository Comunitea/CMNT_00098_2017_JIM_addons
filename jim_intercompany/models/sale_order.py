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
    def action_cancel(self):
        ic_sales = self.env['sale.order'].sudo().search(
            [('auto_purchase_order_id', 'in', self.purchase_ids.mapped('id')),('id', '!=', self.id)])
        if ic_sales:
            for sale in ic_sales:
                sale.action_cancel()
        if self.purchase_ids:
            self.purchase_ids.button_cancel()
        res = super(SaleOrder, self).action_cancel()
        rest_pickings = self.picking_ids.filtered(lambda x: x.state != 'done')
        if rest_pickings:
            rest_pickings.action_cancel()

        return res

    @api.multi
    @api.depends('procurement_group_id')
    def _compute_purchase_ids(self):
        for order in self:
            order.purchase_ids = self.env['purchase.order'].search(
                [('group_id', '=', order.procurement_group_id.id)]) if order.procurement_group_id else []
            order.purchase_count = len(order.purchase_ids)

    @api.multi
    @api.depends('procurement_group_id')
    def _compute_picking_ids(self):
        for order in self:
            order.picking_ids = self.env['stock.picking'].search([('group_id',
                                                                   '=',
                                                                   order.procurement_group_id.id)]) if order.procurement_group_id else []
            if order.purchase_ids:
                for purchase in order.purchase_ids:
                    if purchase.intercompany:
                        ic_sale = self.env['sale.order'].search(
                            [('auto_purchase_order_id', '=',
                              purchase.id)])
                        if ic_sale:
                            order.picking_ids |= ic_sale.picking_ids
            order.delivery_count = len(order.picking_ids)

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

    @api.multi
    def write(self, vals):
        fpos_p = self.env['account.fiscal.position'].sudo()
        paymode_p = self.env['account.payment.mode'].sudo()
        pricelist_p = self.env['product.pricelist'].sudo()
        tax_p = self.env['account.tax'].sudo()
        for order in self:
            if vals.get('company_id', False) and \
                    vals['company_id'] != order.company_id:
                # Search Fiscal position in new company
                if order.fiscal_position_id:
                    domain = [
                        ('name', '=', order.fiscal_position_id.name),
                        ('company_id', '=', vals['company_id'])]
                    fpos = fpos_p.search(domain, limit=1)
                    if fpos:
                        vals['fiscal_position_id'] = fpos.id
                    else:
                        vals['fiscal_position_id'] = \
                            vals.get('fiscal_position_id', False)

                # Search Payment mode in new company
                if order.payment_mode_id:
                    domain = [
                        ('name', '=', order.payment_mode_id.name),
                        ('company_id', '=', vals['company_id'])]
                    paymode = paymode_p.search(domain, limit=1)
                    if paymode:
                        vals['payment_mode_id'] = paymode.id
                    else:
                        vals['payment_mode_id'] = \
                            vals.get('payment_mode_id', False)

                # Search Pricelist in new company
                if order.pricelist_id:
                    domain = [
                        ('name', '=', order.pricelist_id.name),
                        ('company_id', '=', vals['company_id'])]
                    pricelist = pricelist_p.search(domain, limit=1)
                    if pricelist:
                        vals['pricelist_id'] = pricelist.id

                #Search taxes lines in new company
                for line in order.order_line:
                    tax_ids = []
                    for tax in line.tax_id:
                        domain = [
                            ('name', '=', tax.name),
                            ('company_id', '=', vals['company_id'])]
                        new_tax = tax_p.search(domain, limit=1)
                        if new_tax:
                            tax_ids.append(new_tax.id)
                    if tax_ids:
                        line.write({'tax_id': [(6, 0, tax_ids)]})
        if vals.get('company_id', False):
            return super(SaleOrder, self.sudo()).write(vals)
        else:
            return super(SaleOrder, self).write(vals)
