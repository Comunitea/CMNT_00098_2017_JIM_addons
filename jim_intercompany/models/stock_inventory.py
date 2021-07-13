# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class Inventory(models.Model):
    _inherit = "stock.inventory"

    @api.model
    def _default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env["stock.warehouse"].search(
            [("company_id.child_ids", "child_of", company_user.id)], limit=1
        )
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(
                _("You must define a warehouse for the company: %s.")
                % (company_user.name,)
            )

    location_id = fields.Many2one(
        "stock.location",
        "Inventoried Location",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
        default=_default_location_id,
    )
