# © 2016 Comunitea - Kiko <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, _

import odoo.addons.decimal_precision as dp


class HSCodeCountryTax(models.Model):
    _name = "hs.code.country.tax"

    def _get_name(self):
        return self.country_id + ":" + str(self.tax)

    country_id = fields.Many2one(
        "res.country", string="Country", required=True
    )

    tax = fields.Float(
        "Tax", required=True, digits=dp.get_precision("Product Price")
    )
    hs_code_id = fields.Many2one("hs.code", string="HS Code")

    _sql_constraints = [
        (
            "unique_hscode_per_country",
            "unique (country_id, hs_code_id)",
            _("Only one tax per code and country"),
        )
    ]


class HSCode(models.Model):
    _inherit = "hs.code"

    country_tax_ids = fields.One2many(
        "hs.code.country.tax", "hs_code_id", string="Products"
    )
