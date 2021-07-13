# © 2018 Comunitea - Santi Argüeso <santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
import time


class SaleHistory(models.Model):
    _name = "sale.history"

    product_id = fields.Many2one("product.product", "Product", index=1)
    qty = fields.Float("Quantity", default=0.0, required=True)
    date = fields.Date("Date", index=1, help="Date")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.user.company_id.id,
        index=1,
    )
