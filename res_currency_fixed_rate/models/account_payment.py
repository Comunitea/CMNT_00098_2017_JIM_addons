# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez<kiko@xcomunitea.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp


class AccountPayment (models.Model):

    _inherit = "account.payment"

    @api.one
    def get_rate(self):
        self.rate = 0
        if self.company_currency_id and self.currency_id :
            self.rate = self.env["res.currency"].with_context(date=self.payment_date). \
                _get_conversion_rate(self.company_currency_id, self.currency_id)

    @api.depends('currency_id')
    def _same_currency(self):
        for payment in self:
            payment.same_currency = (payment.currency_id == payment.company_currency_id)

    company_currency_id = fields.Many2one('res.currency', string='Company Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    amount_company_currency = fields.Monetary(string='Payment Amount (Company currency)', required=True)
    rate = fields.Float("Exchange rate",
                                       digits=(16, 6), readonly="1", compute=get_rate)
    fixed_rate = fields.Float("Exchange rate",
                                       digits=(16, 6), default=get_rate)
    fixed_rate_bool = fields.Boolean("Manual rate")

    same_currency = fields.Boolean('Same currency', compute="_same_currency")


    @api.onchange('currency_id')
    def onchange_currency_id(self):
        self.onchange_fixed_rate_bool = False
        self.get_rate()
        self.fixed_rate = self.rate
        if self.company_currency_id != self.company_currency_id:
            self.amount_company_currency = self.amount / (self.rate or 1)

    @api.onchange('fixed_rate_bool')
    def onchange_fixed_rate_bool(self):
        if not self.onchange_fixed_rate_bool:
            self.fixed_rate = self.rate

    @api.onchange('fixed_rate', 'amount')
    def onchange_fixed_rate(self):
        self.amount_company_currency = self.amount / (self.fixed_rate or self.rate or 1)

    @api.onchange('amount_company_currency')
    def onchange_amount_company_currency(self):
        if self.amount_company_currency:
            self.fixed_rate = self.amount / self.amount_company_currency

    @api.model
    def create(self, vals):
        currency_id = vals.get('currency_id', False)
        currency = self.env['res.currency'].browse(currency_id)
        if currency_id and currency != self.env.user.company_id.currency_id:
            rate =  self.env["res.currency"].\
                with_context(date=vals.get('payment_date')).\
                _get_conversion_rate(self.env.user.company_id.currency_id, currency)
            vals['amount_company_currency'] = vals.get('amount', 0)/(rate or 1)
        return super(AccountPayment, self).create(vals)

    def _create_payment_entry(self, amount):
        ctx = self._context.copy()
        if self.fixed_rate_bool:
            if not self.fixed_rate:
                raise exceptions.ValidationError(_('You need set exchange rate'))
            ctx['fixed_rate'] = self.fixed_rate
        return super(AccountPayment, self.with_context(ctx))._create_payment_entry(amount)


