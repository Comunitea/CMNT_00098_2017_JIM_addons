# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez<kiko@xcomunitea.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment (models.Model):

    _inherit = "account.payment"

    bank_charge_bool = fields.Boolean('Bank charges')
    bank_charge = fields.Monetary('Amount bank charges', default=0.00)
    bank_charge_account_id = fields.Many2one('account.account', "Bank charge account",
                                             readonly=True)
    @api.onchange('bank_charge_bool')
    def onchange_bank_charge(self):
        if not self.onchange_bank_charge:
            self.bank_charge = 0.00

    def _create_payment_entry(self, amount):

        if not self.journal_id.update_posted:
            raise ValidationError(
                _('You cannot add bank charges in this journal.'
                  'First you should set the journal to allow'
                  ' cancelling entries.'))
        move = super(AccountPayment, self)._create_payment_entry(amount)

        if self.bank_charge_bool:
            move.button_cancel()
            move_credit = move.line_ids.filtered(lambda x: x.account_id == self.journal_id.default_credit_account_id)
            move_credit.credit += self.bank_charge
            loc_currency_id = self.journal_id.bank_account_id.currency_id or self.company_currency_id
            bank_amount_currency = 0.00
            if self.currency_id != loc_currency_id:
                rate = self.currency_id._get_conversion_rate(self.currency_id, loc_currency_id)
                move_credit.amount_currency = -move_credit.credit / rate
                bank_amount_currency = self.bank_charge / rate
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            bank_line_values = {'debit': self.bank_charge,
                                'name': _('Bank charge: %s')%self.name,
                                'payment_id': self.id,
                                'partner_id': False,
                                'currency_id': self.currency_id.id,
                                'move_id': move.id,
                                'amount_currency': bank_amount_currency,
                                'account_id': self.bank_charge_account_id.id}
            aml_obj.create(bank_line_values)
            move.post()
        return move