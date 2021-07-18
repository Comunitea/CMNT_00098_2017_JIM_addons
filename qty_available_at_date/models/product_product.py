# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    at_date = fields.Date("Stock a fecha", store=False)

    def _compute_quantities_dict(
        self, lot_id, owner_id, package_id, from_date=False, to_date=False
    ):

        force_at_date = self._context.get("force_at_date", False)
        if force_at_date:
            from_date = to_date = force_at_date
        return super(ProductProduct, self)._compute_quantities_dict(
            lot_id=lot_id,
            owner_id=owner_id,
            package_id=package_id,
            from_date=from_date,
            to_date=to_date,
        )
