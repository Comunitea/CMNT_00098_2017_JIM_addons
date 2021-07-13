# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    hscode_tax = fields.Float("Tax", digits=dp.get_precision("Product Price"))

    @api.onchange("product_id")
    def onchange_product_id(self):

        res = super(PurchaseOrderLine, self).onchange_product_id()
        if self.product_id:
            country_id = self.order_id.partner_id.country_id
            hs_code = self.product_id.hs_code_id
            domain = [
                ("country_id", "=", country_id.id),
                ("hs_code_id", "=", hs_code.id),
            ]
            tax_id = self.env["hs.code.country.tax"].search(domain)
            tax = tax_id and tax_id[0].tax or 0.00
            self.hscode_tax = tax
        return res
