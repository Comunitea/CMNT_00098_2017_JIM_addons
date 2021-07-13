# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo.exceptions import AccessError, except_orm
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    demand = fields.Float("Demand", readonly=True)
    purchase = fields.Float("Recommended Purchase", readonly=True)

    @api.onchange("product_id")
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        self.product_id.get_purchase_forecast()
        self.demand = self.product_id.demand
        self.purchase = self.product_id.purchase
        return res
