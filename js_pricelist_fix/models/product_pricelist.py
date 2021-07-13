from odoo import api, fields, models


class CustomPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    @api.model
    def create(self, vals):
        # Si se establece un id de variante eliminamos el del producto que se pone por defecto en la plantilla
        if (
            "product_id" in vals
            and "product_tmpl_id" in vals
            and vals["product_id"]
        ):
            del vals["product_tmpl_id"]
        return super(CustomPricelistItem, self).create(vals)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.applied_on = "0_product_variant"
        else:
            self.applied_on = "1_product"
