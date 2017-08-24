# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields, _


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    global_discount_amount = fields.Monetary(
        compute='_compute_global_discount_amount')
    global_discount_percentage = fields.Float('Global discount')

    @api.multi
    def compute_early_payment_lines(self):
        res = super(AccountInvoice, self).compute_early_payment_lines()
        res.write({'promotion_line': True})

    @api.multi
    def apply_global_discount_percentage(self):
        self.ensure_one()
        self.invoice_line_ids.filtered(lambda x: x.global_disc_line).unlink()
        if not self.global_discount_percentage:
            return True
        new_line_vals = {
            'product_id': self.env.ref('commercial_rules.product_discount').id,
            'name': _('Global discount'),
            'promotion_line': True,
            'global_disc_line': True,
            'quantity': 1,
            'account_id': self.invoice_line_ids.with_context(
                journal_id=self.journal_id.id)._default_account(),
            'uom_id': False,
            'invoice_line_tax_ids': False
        }
        new_invoice_line = self.env['account.invoice.line'].new(new_line_vals)
        new_invoice_line._onchange_product_id()
        vals = new_invoice_line._convert_to_write(
                new_invoice_line._cache)
        vals.update(new_line_vals)
        vals['price_unit'] = self.amount_untaxed * \
            (self.global_discount_percentage / 100.0)
        self.write({'invoice_line_ids': [(0, 0, vals)]})

        return True

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
    global_disc_line = fields.Boolean()

    @api.multi
    def _compute_name_report(self):
        for line in self:
            name_report = line.name
            if '[%s]' % line.product_id.default_code in line.name:
                name_report = line.name.replace(
                    '[%s]' % line.product_id.default_code, '')
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
