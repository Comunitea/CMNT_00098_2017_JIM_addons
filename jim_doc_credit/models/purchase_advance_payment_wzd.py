# -*- coding: utf-8 -*-
# Copyright 2015 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class AccountVoucherWizard(models.TransientModel):

    _inherit = "account.purchase.voucher.wizard"

    @api.multi
    def make_report_doc_credit(self):
        # todo revisar por Omar/Santi
        # necesito ponaer un flag aqui en el contexto, parra que al enviar a post no lo haga

        purchase_obj = self.env['purchase.order']
        purchase_ids = self.env.context.get('active_ids', [])
        if purchase_ids:
            purchase_id = purchase_ids[0]
            purchase = purchase_obj.browse(purchase_id)

        fields_to_check = ('proforma_invoice_ref', 'proforma_invoice_date',
                           'limit_expedition_date', 'mail_confirm_packing_list',
                           'partner_bank_contact_id', 'expire_credit_letter_date',
                           'incoterm_id', 'doc_credit_bank_id', 'in_port_id')
        for field in fields_to_check:
            if purchase[field] == False:
                raise ValidationError ("You must fill this fields\n%s"%str(fields_to_check))



        self = self.with_context(not_payment_post=True)
        res = super(AccountVoucherWizard, self).make_advance_payment()

        payment_obj = self.env['account.payment']
        payment = payment_obj.search([('purchase_id', '=', purchase_id)], limit=1, order="id desc")
        report = payment.create_doc_credit()
        payment.write({'doc_credit': 'Documentary credit :' + str(payment.id) + '.pdf'})
        return res


class AccountPayment(models.Model):

    _inherit = "account.payment"

    doc_credit = fields.Char("Documentary credit ref")

    @api.multi
    def create_doc_credit(self):

        report = self.env['report'].get_action(self, 'jim_doc_credit.doc_credit')
        #payment.write({'doc_credit': 'Documentary credit :' + payment.id + '.pdf'})
        return report

