# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    name_report = fields.Char(compute='_compute_name_report')

    @api.multi
    def _compute_name_report(self):
        for line in self:
            name_report = line.name
            if '[%s]' % line.product_id.default_code in line.name:
                name_report = line.name.replace('[%s]' % line.product_id.default_code, '')
            line.name_report = name_report


    @api.multi
    def get_custom_qty_price(self, qty):
        self.ensure_one()
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price, currency, qty, product=self.product_id,
                partner=self.invoice_id.partner_id)
        return taxes['total_excluded'] if taxes else qty * price
