# Copyright 2015 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _


class AccountPayment(models.Model):

    _inherit = "account.payment"

    forecast_move_id = fields.Many2one(
        "account.move", "Forecast Move", readonly=True
    )

    @api.multi
    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        for payment in self:
            if "payment_date" in vals and payment.forecast_move_id:
                payment.forecast_move_id.line_ids.write(
                    {"date_maturity": vals["payment_date"]}
                )

            if "amount_company_currency" in vals and payment.forecast_move_id:
                ctx = self._context.copy()
                ctx.update(check_move_validity=False)
                for line in payment.forecast_move_id.with_context(
                    ctx
                ).line_ids:
                    if line.debit > 0:
                        line.debit = vals["amount_company_currency"]
                        if (
                            self.company_id.currency_id.id
                            != self.currency_id.id
                        ):
                            line.amount_currency = vals["amount"]
                    if line.credit > 0:
                        line.credit = vals["amount_company_currency"]
                        if (
                            self.company_id.currency_id.id
                            != self.currency_id.id
                        ):
                            line.amount_currency = -vals["amount"]

        return res

    def create_forecast_entry(
        self,
    ):
        """Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
        Return the journal entry.
        """
        amount = self.amount
        aml_obj = self.env["account.move.line"].with_context(
            check_move_validity=False
        )

        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.payment_date
        ).compute_amount_fields(
            amount, self.currency_id, self.company_id.currency_id, False
        )

        forecast_journal = self.company_id.forecast_journal_id
        move = self.env["account.move"].create(
            self._get_move_vals(forecast_journal)
        )

        # Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(
            credit, debit, -amount_currency, move.id, False
        )
        counterpart_aml_dict.update(
            self._get_counterpart_move_line_vals(self.invoice_ids)
        )
        counterpart_aml_dict.update(
            {"currency_id": currency_id, "received_issued": True}
        )
        aml_obj.create(counterpart_aml_dict)

        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(
            debit, credit, amount_currency, move.id, False
        )
        liquidity_aml_dict.update(self._get_forecast_move_line_vals(amount))
        aml_obj.create(liquidity_aml_dict)

        self.forecast_move_id = move

    def _get_forecast_move_line_vals(self, amount):
        name = self.name
        vals = {
            "name": name,
            "account_id": self.payment_type in ("outbound", "transfer")
            and self.company_id.forecast_journal_id.default_debit_account_id.id
            or self.company_id.forecast_journal_id.default_credit_account_id.id,
            "payment_id": self.id,
            "journal_id": self.company_id.forecast_journal_id.id,
            "currency_id": self.currency_id != self.company_id.currency_id
            and self.currency_id.id
            or False,
            #'received_issued': True,
        }

        # If the journal has a currency specified, the journal item need to be expressed in this currency
        if (
            self.journal_id.currency_id
            and self.currency_id != self.journal_id.currency_id
        ):
            amount = self.currency_id.with_context(
                date=self.payment_date
            ).compute(amount, self.journal_id.currency_id)
            debit, credit, amount_currency, dummy = (
                self.env["account.move.line"]
                .with_context(date=self.payment_date)
                .compute_amount_fields(
                    amount,
                    self.journal_id.currency_id,
                    self.company_id.currency_id,
                )
            )
            vals.update(
                {
                    "amount_currency": amount_currency,
                    "currency_id": self.journal_id.currency_id.id,
                }
            )

        return vals

    def post(self):
        if self.forecast_move_id:
            self.forecast_move_id.unlink()
        super(AccountPayment, self).post()
