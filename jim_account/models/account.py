# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def get_mandate_scheme(self):
        for line in self:
            if line.move_id.mandate_id:
                line.scheme = line.move_id.mandate_id.scheme
            else:
                line.scheme = False

    @api.model
    def _mandate_scheme_search(self, operator, operand):

        moves = self.search([("move_id.mandate_id.scheme", operator, operand)])
        return [("id", "in", moves.mapped("id"))]

    scheme = fields.Selection(
        selection=[("CORE", "Basic (CORE)"), ("B2B", "Enterprise (B2B)")],
        string="Scheme",
        compute="get_mandate_scheme",
        search="_mandate_scheme_search",
    )
    payment_order_line_ids = fields.One2many(
        "account.payment.line",
        "move_line_id",
        string="Payment Line",
        readonly=True,
    )


class AccountMove(models.Model):

    _inherit = "account.move"

    user_id = fields.Many2one(
        states={
            "draft": [("readonly", False)],
            "open": [("readonly", False)],
            "paid": [("readonly", False)],
        }
    )
    #TODO: Migrar
    #invoice_line_ids = fields.One2many(readonly=False)

    def action_invoice_paid(self):
        super_invoices = self.filtered(lambda inv: inv.amount_total != 0)
        return super(AccountMove, super_invoices).action_invoice_paid()


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    #TODO: Migrar
    # ~ state = fields.Selection(
        # ~ [
            # ~ ("draft", "Draft"),
            # ~ ("proforma", "Pro-forma"),
            # ~ ("proforma2", "Pro-forma"),
            # ~ ("open", "Open"),
            # ~ ("paid", "Paid"),
            # ~ ("cancel", "Cancelled"),
        # ~ ],
        # ~ related="invoice_id.state",
    # ~ )

    def unlink(self):
        if any(self.filtered(lambda r: r.state in ("open", "paid"))):
            raise UserError(
                _("No se pueden eliminar lineas de facturas abiertas")
            )
        return super().unlink()
