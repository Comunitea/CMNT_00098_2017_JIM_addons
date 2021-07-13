# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

ORDER_LINE_INC = 1000


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    template_sequence = fields.Integer("Template sequence")


class PurchaseOder(models.Model):

    _inherit = "purchase.order"

    def reorder_sequence(self):
        templates = self.order_line.mapped("product_id").mapped(
            "product_tmpl_id"
        )
        for template in templates:
            template_lines = self.order_line.filtered(
                lambda x: x.product_id.product_tmpl_id == template
            ).sorted(key=lambda x: x.template_sequence)
            template_sequence = template_lines[0].template_sequence
            for order in template_lines:
                vals = {
                    "sequence": order.product_id.get_variant_sequence(
                        sequence_origin=template_sequence
                    ),
                    "template_sequence": template_sequence,
                }
                order.write(vals)
