# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    #TODO: Migrar, no existe el modelo product.attribute.value
    # ~ color_id = fields.Many2one(
        # ~ "product.attribute.value", "Color", readonly=True
    # ~ )
    # ~ size_id = fields.Many2one("product.attribute.value", "Size", readonly=True)
    ref = fields.Char(string="Empresa  Ref", readonly=True)
    commercial_partner_ref = fields.Char(
        string="Empresa asociada. Ref", readonly=True
    )

    def _select(self):
        res = super(AccountInvoiceReport, self)._select()
        res = (
            res
            #TODO: Migrar, no existe el modelo product.attribute.value
            # ~ + """,
                        # ~ (SELECT pav.id FROM product_attribute_value pav INNER JOIN product_attribute_value_product_product_rel pavppr
                                # ~ on pavppr.product_attribute_value_id = pav.id
                                # ~ INNER JOIN  product_attribute pa on pav.attribute_id = pa.id
                                # ~ WHERE pavppr.product_product_id = product_id and pa.is_color = True LIMIT 1)
                 # ~ as color_id,
                        # ~ (SELECT pav.id FROM product_attribute_value pav INNER JOIN product_attribute_value_product_product_rel pavppr
                                # ~ on pavppr.product_attribute_value_id = pav.id
                                # ~ INNER JOIN  product_attribute pa on pav.attribute_id = pa.id
                                # ~ WHERE pavppr.product_product_id = product_id and pa.is_color = False LIMIT 1)
                 # ~ as size_id,
                 + """, ai_partner.ref || ' - ' || ai_partner.name as ref,
                 partner.ref || ' - ' || partner.name as commercial_partner_ref
                        """
        )
        return res

    def _from(self):
        res = super(AccountInvoiceReport, self)._from()
        res = (
            res
            + """ join res_partner ai_partner on move.partner_id = ai_partner.id """
        )
        return res

    def _group_by(self):
        res = super(AccountInvoiceReport, self)._group_by()
        res = (
            res
            + """, partner.ref, partner.name, ai_partner.name, ai_partner.ref """
        )
        return res
