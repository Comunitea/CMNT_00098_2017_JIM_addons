# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_moves(self, picking):

        if self._context.get("force_procurement", False):
            for procurement in self.procurement_ids.filtered(
                lambda p: p.state == "cancel"
            ):
                procurement.reset_to_confirmed()
        return super(PurchaseOrderLine, self)._prepare_stock_moves(picking)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        # Si no viene desde el wzd
        if not "force_procurement" in self._context.keys():
            purchase_ids = self.env["purchase.order"]
            canceled_procurement_ids = self.env["procurement.order"]
            for purchase in self:
                canceled_proc = self.env["procurement.order"]
                for line in purchase.order_line:
                    canceled_proc = line.procurement_ids.filtered(
                        lambda p: p.state == "cancel" and p.rule_id.id == 141
                    )
                if canceled_proc:
                    purchase_ids += purchase
                    canceled_procurement_ids += canceled_proc
            if purchase_ids:
                view = self.env.ref(
                    "reconfirm_procurement_canceled_po.wzd_confirm_procurement"
                )
                wiz = self.env["wzd.confirm.procurement"].create(
                    {
                        "purchase_ids": [(4, purchase_ids.ids, 0)],
                        "procurement_ids": [
                            (4, canceled_procurement_ids.ids, 0)
                        ],
                    }
                )
                return {
                    "name": _("Reconfirm canceled procurement"),
                    "type": "ir.actions.act_window",
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "wzd.confirm.procurement",
                    "views": [(view.id, "form")],
                    "view_id": view.id,
                    "target": "new",
                    "res_id": wiz.id,
                    "context": self.env.context,
                }
        res = super(PurchaseOrder, self).button_confirm()
        return res
