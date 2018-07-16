# -*- coding: utf-8 -*-
# © 201t Comunitea (Santi Argüeso - santi@comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'



    @api.multi
    def _prepare_move_line_offsetting_account(
            self, amount_company_currency, amount_payment_currency,
            bank_lines):
        vals = super(AccountPaymentOrder, self
                     )._prepare_move_line_offsetting_account(amount_company_currency, amount_payment_currency,
            bank_lines)
        vals.update({
                'received_issued': True,
                })
        return vals