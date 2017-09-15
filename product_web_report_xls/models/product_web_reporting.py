# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _report_xls_document_extra(self):
        """Inherit this for adding/changing document references.
        """
        return ""

    def _report_xls_fields(self):
        """Inherit this for adding/changing fields to export to XLS file.
        """
        return [
            'display_name',  # account.balance.reporting.line, name
            'default_code',
            'tag_names',
            'web',
            'global_real_stock',
        ]

    def _report_xls_template(self):
        """Inherit this for adding/changing template entries.
        """
        return {}
