# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _


class AccountMove(models.Model):

    _inherit = "account.move"

    notes = fields.Text()
    show_associated = fields.Boolean(compute="_compute_show_associated")

    def _compute_show_associated(self):
        def _get_parent_company(partner):
            if not partner.is_company and partner.parent_id:
                return _get_parent_company(partner.parent_id)
            return partner

        for invoice in self:
            if invoice.partner_id != invoice.commercial_partner_id:
                partner_parent = _get_parent_company(invoice.partner_id)
                commercial_partner_parent = _get_parent_company(
                    invoice.commercial_partner_id
                )
                if partner_parent != commercial_partner_parent:
                    invoice.show_associated = True
                else:
                    invoice.show_associated = False
            else:
                invoice.show_associated = False


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    global_disc_line = fields.Boolean()

    def get_custom_qty_price(self, qty):
        self.ensure_one()
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price,
                currency,
                qty,
                product=self.product_id,
                partner=self.invoice_id.partner_id,
            )
        return taxes["total_excluded"] if taxes else qty * price


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    report_refund_warning = fields.Text(translate=True)
