# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    risk_sale_order_include = fields.Boolean(
        string="Include Sales Orders",
        company_dependent=True,
        help="Full risk computation",
    )
    risk_sale_order_limit = fields.Float(
        string="Limit Sales Orders",
        company_dependent=True,
        help="Set 0 if it is not locked",
    )

    risk_invoice_draft_include = fields.Boolean(
        string="Include Draft Invoices",
        company_dependent=True,
        help="Full risk computation",
    )
    risk_invoice_draft_limit = fields.Float(
        string="Limit In Draft Invoices",
        company_dependent=True,
        help="Set 0 if it is not locked",
    )

    risk_invoice_open_include = fields.Boolean(
        string="Include Open Invoices/Principal Balance",
        company_dependent=True,
        help="Full risk computation.\n"
        "Residual amount of move lines not reconciled with the same "
        "account that is set as partner receivable and date maturity "
        "not exceeded, considering Due Margin set in account settings.",
    )
    risk_invoice_open_limit = fields.Float(
        string="Limit In Open Invoices/Principal Balance",
        company_dependent=True,
        help="Set 0 if it is not locked",
    )

    risk_invoice_unpaid_include = fields.Boolean(
        string="Include Unpaid Invoices/Principal Balance",
        company_dependent=True,
        help="Full risk computation.\n"
        "Residual amount of move lines not reconciled with the same "
        "account that is set as partner receivable and date maturity "
        "exceeded, considering Due Margin set in account settings.",
    )
    risk_invoice_unpaid_limit = fields.Float(
        string="Limit In Unpaid Invoices/Principal Balance",
        company_dependent=True,
        help="Set 0 if it is not locked",
    )

    risk_account_amount_include = fields.Boolean(
        string="Include Other Account Open Amount",
        company_dependent=True,
        help="Full risk computation.\n"
        "Residual amount of move lines not reconciled with distinct "
        "account that is set as partner receivable and date maturity "
        "not exceeded, considering Due Margin set in account settings.",
    )
    risk_account_amount_limit = fields.Float(
        string="Limit Other Account Open Amount",
        company_dependent=True,
        help="Set 0 if it is not locked",
    )

    risk_account_amount_unpaid_include = fields.Boolean(
        string="Include Other Account Unpaid Amount",
        company_dependent=True,
        help="Full risk computation.\n"
        "Residual amount of move lines not reconciled with distinct "
        "account that is set as partner receivable and date maturity "
        "exceeded, considering Due Margin set in account settings.",
    )
    risk_account_amount_unpaid_limit = fields.Float(
        string="Limit Other Account Unpaid Amount",
        company_dependent=True,
        help="Set 0 if it is not locked",
    )
