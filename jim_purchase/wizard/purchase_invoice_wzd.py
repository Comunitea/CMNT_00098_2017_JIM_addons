# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api,_
from openerp.exceptions import ValidationError

class PurchaseOrderInvoiceWzd(models.TransientModel):
    _name ="purchase.invoice.lines.wzd"

    @api.model
    def get_picking_state(self):
        return [
            ('draft', ''),
            ('cancel', 'Cancelled'),
            ('not_received', 'Not Received'),
            ('partially_received', 'Partially Received'),
            ('done', 'Transferred'),
        ]
    purchase_invoice_id = fields.Many2one('purchase.invoice.wzd')

    order_id = fields.Many2one('purchase.order')
    name = fields.Char("Name")
    partner_ref = fields.Char('Vendor Reference', copy=False,\
        help="Reference of the sales order or bid sent by the vendor. "
             "It's used to do the matching when you receive the "
             "products as this reference is usually written on the "
             "delivery order sent by your vendor.")
    date_order = fields.Datetime('Order Date',
                                 help="Depicts the date where the Quotation should be validated and converted into a purchase order.")
    origin = fields.Char('Source Document', help="Reference of the document that generated this purchase order "
             "request (e.g. a sale order or an internal procurement request)")

    amount_untaxed = fields.Monetary(string='Untaxed Amount')
    amount_tax = fields.Monetary(string='Taxes')
    amount_total = fields.Monetary(string='Total')
    currency_id = fields.Many2one('res.currency', 'Currency')
    picking_state = fields.Char(
        string="Picking status",
        help="Overall status based on all pickings")
    selected = fields.Boolean("To invoice", default=False)


class PurchaseInvoiceWzd(models.TransientModel):
    _name = "purchase.invoice.wzd"

    partner_id = fields.Many2one('res.partner', string='Vendor')
    purchase_order_ids = fields.One2many('purchase.invoice.lines.wzd', 'purchase_invoice_id', string="Purchase orders")
    account_invoice_id = fields.Many2one('account.invoice')

    @api.model
    def default_get(self, fields):

        res = super(PurchaseInvoiceWzd, self).default_get(fields)
        partner_id = self.env.context.get('partner_id', False)
        domain = ([('partner_id','=',partner_id), ('invoice_status','=','to invoice')])
        order_ids = self.env['purchase.order'].search(domain)
        orders = []

        if not order_ids:
            return res
        for order in order_ids:
            orders.append([0,0,{'order_id': order.id,
                                'name': order.name,
                                'date_order': order.date_order,
                                'origin': order.origin,
                                'partner_ref': order.partner_ref,
                                'amount_untaxed': order.amount_untaxed,
                                'amount_tax':order.amount_tax,
                                'amount_total': order.amount_total,
                                'currency_id': order.currency_id.id,
                                'picking_state': order.picking_state
                                }])
        res['purchase_order_ids'] = orders
        return res

    def select_all(self):
        self.purchase_order_ids.write({'selected': True})
        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'nodestroy': True,
        }

    def select_none(self):
        self.purchase_order_ids.write({'selected': False})
        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'nodestroy': True,
        }

    def add_to_invoice_order(self):
        orders = []
        invoice_id = self.env['account.invoice'].browse(self.account_invoice_id.id)
        new_lines = self.env['account.invoice.line']


        for order in self.purchase_order_ids.filtered(lambda x: x.selected):
            invoice_id.purchase_id = order.order_id
            invoice_id.purchase_order_change()
            invoice_id._onchange_invoice_line_ids()
        invoice_id._onchange_origin()