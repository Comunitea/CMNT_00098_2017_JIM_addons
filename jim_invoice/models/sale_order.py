# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    force_invoiced_status = fields.Boolean("Marcar como facturado")

    @api.depends("state", "order_line.invoice_status", "force_invoiced_status")
    def _get_invoiced(self):
        res = super(SaleOrder, self)._get_invoiced()
        for order in self:
            if order.state in ("sale", "done") and order.force_invoiced_status:
                order.update({"invoice_status": "invoiced"})
        return res
