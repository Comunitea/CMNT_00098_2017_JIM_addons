# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _


class AccountMove(models.Model):

    _inherit = "account.move"

    global_discount_amount = fields.Monetary(
        compute="_compute_global_discount_amount"
    )
    global_discount_percentage = fields.Float("Global discount")
    notes = fields.Text()
    show_associated = fields.Boolean(compute="_compute_show_associated")

    def compute_early_payment_lines(self):
        res = super().compute_early_payment_lines()
        res.write({"promotion_line": True})

    def apply_global_discount_percentage(self):
        self.ensure_one()
        self.invoice_line_ids.filtered(lambda x: x.global_disc_line).unlink()
        if not self.global_discount_percentage:
            return True
        new_line_vals = {
            "product_id": self.env.ref("commercial_rules.product_discount").id,
            "name": _("Global discount"),
            "promotion_line": True,
            "global_disc_line": True,
            "quantity": 1,
            "account_id": self.invoice_line_ids.with_context(
                journal_id=self.journal_id.id
            )._default_account(),
            "uom_id": False,
            "invoice_line_tax_ids": False,
        }
        new_invoice_line = self.env["account.invoice.line"].new(new_line_vals)
        new_invoice_line._onchange_product_id()
        vals = new_invoice_line._convert_to_write(new_invoice_line._cache)
        vals.update(new_line_vals)
        vals["price_unit"] = self.amount_untaxed * (
            self.global_discount_percentage / 100.0
        )
        self.write({"invoice_line_ids": [(0, 0, vals)]})

        return True

    def _compute_global_discount_amount(self):
        for invoice in self:
            global_discount_lines = invoice.invoice_line_ids.filtered(
                lambda x: x.promotion_line
            )
            if global_discount_lines:
                invoice.global_discount_amount = sum(
                    global_discount_lines.mapped("price_subtotal")
                )
            else:
                invoice.global_discount_amount = 0.0

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

    name_report = fields.Char(compute="_compute_name_report")
    promotion_line = fields.Boolean("Rule Line")
    global_disc_line = fields.Boolean()

    def _compute_name_report(self):
        for line in self:
            name_report = line.name
            if "[%s]" % line.product_id.default_code in line.name:
                name_report = line.name.replace(
                    "[%s]" % line.product_id.default_code, ""
                )
            line.name_report = name_report

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
