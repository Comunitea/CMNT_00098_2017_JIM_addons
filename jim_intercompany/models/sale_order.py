# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    move_dest_IC_id = fields.Many2one('stock.move', 'Destination Move IC',
                                      copy=False, index=True,
                                      help="Optional: next IC stock move when "
                                           "chaining them")
    purchase_line_IC = fields.Many2one('purchase.order.line',
                                       'Related purchase line', copy=False,
                                       index=True)

    def _prepare_order_line_procurement(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_order_line_procurement(
            group_id)
        vals['move_dest_IC_id'] = self.move_dest_IC_id.id
        vals['purchase_line_IC'] = self.purchase_line_IC.id
        return vals


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    purchase_ids = fields.Many2many('purchase.order', compute='_compute_purchase_ids',
                                   string='Purchases associated to this sale')
    purchase_count = fields.Integer(string='Purchases', compute='_compute_purchase_ids')
    procurement_groups = fields.Many2many('procurement.group', compute='_compute_procurements')
    mrp_productions = fields.Many2many('mrp.production', compute='_compute_mrp_productions')
    mrp_productions_count = fields.Integer(compute='_compute_mrp_productions')

    @api.one
    def _prepare_purchase_order_data(self, company, company_partner):
        """ Generate purchase order values, from the SO (self)
            :param company_partner : the partner representing the company of the SO
            :rtype company_partner : res.partner record
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # find location and warehouse, pick warehouse from company object
        PurchaseOrder = self.env['purchase.order']
        warehouse = company.warehouse_id
        if not warehouse:
            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))

        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'), ('warehouse_id', '=', warehouse.id)
        ], limit=1)
        if not picking_type_id:
            intercompany_uid = company.intercompany_user_id.id
            picking_type_id = PurchaseOrder.sudo(intercompany_uid)._default_picking_type()
        res = {
            'name': self.env['ir.sequence'].sudo().next_by_code('purchase.order'),
            'origin': self.name,
            'partner_id': company_partner.id,
            'picking_type_id': picking_type_id.id,
            'date_order': self.date_order,
            'company_id': company.id,
            'fiscal_position_id': company_partner.property_account_position_id.id,
            'payment_term_id': company_partner.property_supplier_payment_term_id.id,
            'auto_generated': True,
            'auto_sale_order_id': self.id,
            'partner_ref': self.name,
        }
        return res


    @api.depends('procurement_group_id')
    def _compute_procurements(self):
        for order in self:
            procurements = order.procurement_group_id
            for purchase in order.purchase_ids:
                if purchase.intercompany:
                    ic_sale = self.env['sale.order'].search(
                        [('auto_purchase_order_id', '=',
                          purchase.id)])
                    if ic_sale:
                        procurements |= ic_sale.mapped('procurement_group_id')
            order.procurement_groups = procurements

    @api.depends('procurement_group_id')
    def _compute_mrp_productions(self):
        for order in self:
            order.mrp_productions = self.env['mrp.production'].search([('procurement_group_id', 'in', order.procurement_groups.ids)])
            order.mrp_productions_count = len(order.mrp_productions)

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
                                                                   'in',
                                                                   order.procurement_groups.ids)]) if order.procurement_groups else []
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
    def action_view_productions(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]

        productions = self.mapped('mrp_productions')
        if len(productions) > 1:
            action['domain'] = [('id', 'in', productions.ids)]
        elif productions:
            action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            action['res_id'] = productions.id
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

                if 'company_id' in vals:
                    vals['name'] = self.env['ir.sequence'].with_context(
                            force_company=vals['company_id']).next_by_code(
                            'sale.order') or _('New')


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
