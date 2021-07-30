# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

# import barcode#

ORDER_LINE_INC = 1000


class SaleOrderLineTemplate(models.Model):
    _inherit = "sale.order.line.template"
    _order = "order_id, layout_category_id, sequence, id"


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"
    _order = "order_id, layout_category_id, template_sequence, sequence, id"

    template_sequence = fields.Integer(
        related="template_line.sequence", store=True
    )

    @api.model
    def create(self, vals):
        line = super(SaleOrderLine, self).create(vals)
        if not line.product_id.product_template_attribute_value_ids:
            line.sequence = line.template_sequence
        else:
            new_sequence = 0
            cent = 100
            for value in line.product_id.product_template_attribute_value_ids:
                if value.attribute_id.is_color:
                    new_sequence += value.id * ORDER_LINE_INC
                else:
                    new_sequence += value.sequence * cent
                cent = 1
            line.sequence = new_sequence
        return line
