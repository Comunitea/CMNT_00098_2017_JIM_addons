# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    def _get_claim_ids(self):
        for invoice in self:
            invoice.claim_ids = self.env['crm.claim'].search([('invoice_id', '=', self.id)])

    claim_ids = fields.One2many('crm.claim', string='Claims RMA', compute=_get_claim_ids)

    def open_this_invoice(self):

        if self.type in ('out_refund', 'out_invoice'):
            form_view_ref = self.env.ref('account.invoice_form', False)
            tree_view_ref = self.env.ref('account.invoice_tree', False)
        else:
            form_view_ref = self.env.ref('account.invoice_supplier_form', False)
            tree_view_ref = self.env.ref('account.invoice_supplier_tree', False)


        res= {'type': 'ir.actions.act_window',
         'name': ('Factura'),
         'view_mode': 'form, tree',
         'view_type': 'form',
         'res_model': 'account.invoice',
         'views': [(form_view_ref.id, 'form')],
         'target': 'current',
         'res_id': self.id
         }
        return res

    @api.multi
    def unlink(self):
        claim_ids = self.env['crm.claim']
        for invoice in self:
            claim_ids |= invoice.claim_ids
        res = super(AccountInvoice, self).unlink()
        if claim_ids:
            claim_ids._get_invoiced()
        return res
