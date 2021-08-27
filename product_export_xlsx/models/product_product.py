# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _report_xls_fields(self):
        """
        Adapt list in custom module to add/drop columns or change order.
        """
        return [
            "display_name",
            "default_code",
            "website_published",
            "tag_names",
            "web_global_stock",
        ]

    @api.model
    def _report_xls_template(self):
        """
        Template updates, e.g.

        tmpl_upd = super(AccountInvoiceLine, self)._report_xls_template()
        tmpl_upd.update({
            'note': {
                'header': [1, 42, 'text', _render("_('Notes')")],
                'lines': [1, 0, 'text', _render("line.note or ''")],
                'totals': [1, 0, 'text', None]},
        }
        return tmpl_upd
        """
        return {}
