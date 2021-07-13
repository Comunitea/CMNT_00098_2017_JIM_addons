# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ForecastPurchaseLineWizard(models.TransientModel):
    _name = "forecast.purchase.line.wizard"

    product_id = fields.Many2one("product.product")
    product_qty = fields.Float("Quantity", default=0.00)
    product_purchase_wzd_id = fields.Many2one("forecast.purchase.wizard")


class ForecastPurchaseWizard(models.TransientModel):

    _name = "forecast.purchase.wizard"
    seller_id = fields.Many2one("res.partner", "Seller", required=True)
    purchase_order = fields.Many2one("purchase.order")
    line_ids = fields.One2many(
        "forecast.purchase.line.wizard", "product_purchase_wzd_id", "Lines"
    )

    def add_to_purchase_order(self):

        if not self.purchase_order:
            raise ValidationError(_("No order selected"))
        order_line = self.env["purchase.order.line"]
        ids = [x.product_id.id for x in self.line_ids]
        domain = [
            ("order_id", "=", self.purchase_order.id),
            ("product_id", "in", ids),
        ]
        lines_to_unlink = self.env["purchase.order.line"].search(domain)
        lines_to_unlink.unlink()

        for line in self.line_ids:
            order_line = order_line.new(
                {
                    "product_id": line.product_id.id,
                    "product_uom": line.product_id.uom_id,
                    "order_id": self.purchase_order.id,
                    "product_qty": line.product_qty,
                }
            )
            order_line.onchange_product_id()
            order_line.product_qty = line.product_qty
            order_line_vals = order_line._convert_to_write(order_line._cache)
            self.purchase_order.order_line.create(order_line_vals)

        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "purchase.order",
            "type": "ir.actions.act_window",
            "res_id": self.purchase_order.id,
            "context": self.env.context,
        }

    @api.model
    def default_get(self, fields):
        res = super(ForecastPurchaseWizard, self).default_get(fields)
        line_ids = self.env.context.get("active_ids", [])
        line_objs = self.env["purchase.forecast.line"].browse(line_ids)

        lines = []
        if not line_objs:
            return res
        for line in line_objs:
            lines.append(
                {"product_id": line.product_id.id, "product_qty": line.to_buy}
            )

        if line_objs[0].forecast_id.seller_id:
            res["seller_id"] = line_objs[0].forecast_id.seller_id.id

        res["line_ids"] = map(lambda x: (0, 0, x), lines)
        return res
