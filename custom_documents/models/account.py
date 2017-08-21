# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    global_discount_amount = fields.Monetary(
        compute='_compute_global_discount_amount')

    @api.multi
    def _compute_global_discount_amount(self):
        for invoice in self:
            global_discount_lines = invoice.invoice_line_ids.filtered(
                lambda x: x.promotion_line)
            if global_discount_lines:
                invoice.global_discount_amount = sum(
                    global_discount_lines.mapped('price_subtotal'))
            else:
                invoice.global_discount_amount = 0.0

class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    name_report = fields.Char(compute='_compute_name_report')
    promotion_line = fields.Boolean("Rule Line")

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
