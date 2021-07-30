from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    active_category = fields.Boolean(
        related="product_categ_id.active", string="Active (category)"
    )
