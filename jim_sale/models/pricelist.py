# © 2020 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from datetime import datetime

import logging

_logger = logging.getLogger("--EXPORTACIÓN PRECIOS--")


class ProductPricelistItem(models.Model):

    _inherit = "product.pricelist.item"

    def button_edit_items(self):
        self.ensure_one()
        view = self.env.ref("product.product_pricelist_item_form_view")
        ctx = self.env.context.copy()
        ctx.update(default_pricelist_id=self.pricelist_id.id)
        return {
            "name": _("Agents"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "current",
            "res_id": self.id,
            "context": ctx,
        }
