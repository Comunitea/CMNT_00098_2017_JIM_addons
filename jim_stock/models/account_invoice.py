# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    arancel_percentage = fields.Float()
    #TODO: Migrar
    # ~ arancel = fields.Float(compute="_compute_arancel", store=True)

    # ~ @api.depends("price_subtotal", "quantity", "arancel_percentage")
    # ~ def _compute_arancel(self):
        # ~ for line in self:
            # ~ if line.arancel_percentage:
                # ~ line.arancel = (line.price_subtotal / line.quantity) * (
                    # ~ line.arancel_percentage / 100
                # ~ )
            # ~ else:
                # ~ line.arancel = 0

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.move_id and res.move_id.state != "draft":
            raise UserError(
                "Solo se pueden añadir lineas a facturas en "
                "estado borrador. Descarte los cambios cancele "
                "la factura y sitúela en "
                "estado borrador para realizar esta operación"
            )
        return res


class AccountMove(models.Model):

    _inherit = "account.move"

    delivery_cost = fields.Float()
