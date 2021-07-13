# Copyright 2017 Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
from odoo import api, models, fields

ORDER_LINE_INC = 1000


class PurchaseManageVariant(models.TransientModel):
    _inherit = "purchase.manage.variant"

    template_sequence = fields.Integer("Template sequence")

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        if self._context.get("default_template_sequence", False):
            return super(
                PurchaseManageVariant, self
            )._onchange_product_tmpl_id()

        if not self.product_tmpl_id:
            return

        context = self.env.context
        record = self.env[context["active_model"]].browse(context["active_id"])
        if context["active_model"] == "purchase.order.line":
            purchase_order = record.order_id
        else:
            purchase_order = record
        self.template_sequence = (
            max(purchase_order.order_line.mapped("template_sequence")) + 1
        )
        return super(PurchaseManageVariant, self)._onchange_product_tmpl_id()

    @api.multi
    def button_transfer_to_order(self):

        res = super(PurchaseManageVariant, self).button_transfer_to_order()
        context = self.env.context
        record = self.env[context["active_model"]].browse(context["active_id"])
        if context["active_model"] == "purchase.order.line":
            purchase_order = record.order_id
        else:
            purchase_order = record
        for line in purchase_order.order_line.filtered(
            lambda x: x.product_id.product_tmpl_id == self.product_tmpl_id
        ):
            sequence = line.product_id.get_variant_sequence(
                sequence_origin=self.template_sequence
            )
            vals = {
                "sequence": sequence,
                "template_sequence": self.template_sequence,
            }
            line.write(vals)
        return res
