# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    date_planned_date = fields.Date(compute="_compute_date_planned_date")

    @api.depends("date_planned")
    def _compute_date_planned_date(self):
        for purchase in self:
            purchase.date_planned_date = purchase.date_planned.split(" ")[0]

