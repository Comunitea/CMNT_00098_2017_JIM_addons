# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    date_planned_date = fields.Date(compute="_compute_date_planned_date")
    name_report = fields.Text(compute="_compute_name_report")

    @api.depends("date_planned")
    def _compute_date_planned_date(self):
        for purchase in self:
            purchase.date_planned_date = purchase.date_planned.split(" ")[0]

    def _compute_name_report(self):
        for line in self:
            name_report = line.name
            if "[%s]" % line.product_id.default_code in line.name:
                name_report = line.name.replace(
                    "[%s]" % line.product_id.default_code, ""
                )
            line.name_report = name_report
