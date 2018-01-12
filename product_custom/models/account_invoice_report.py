# -*- coding: utf-8 -*-


from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    active_category = fields.Boolean(related="categ_id.active", string="Active (category)")
