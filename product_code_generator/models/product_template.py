# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductAttribute(models.Model):

    _inherit = 'product.attribute'

    is_color = fields.Boolean("Represents a color")


class ProductAttributeValue(models.Model):

    _inherit = 'product.attribute.value'

    code = fields.Char("Code", help="Code number for this variant")
    is_color = fields.Boolean("Represents a color",
                              related="attribute_id.is_color")

    _sql_constraints = [
        ('attribute_code_unique', 'unique(code, attribute_id)',
         'Code must be unique per attribute!'),
    ]



class ProductProduct(models.Model):

    _inherit = 'product.product'

    template_code = fields.Char(related="product_tmpl_id.template_code")

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    template_code = fields.Char("Template code", size=45)
    
    @api.onchange('default_code')
    def onchange_default_code(self):
        self.template_code = self.default_code

    @api.multi
    def create_variant_ids(self):
        code = {}
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            default_code = template.product_variant_ids.default_code
            code[template.id] = default_code
        for template in (self - unique_variants):
            default_code = template.product_variant_ids and \
                           template.product_variant_ids[0].default_code.split('.')[0] \
                           or template.default_code
            code[template.id] = default_code

        res = super(ProductTemplate, self).create_variant_ids()

        for tmpl_id in self.with_context(active_test=False).\
                filtered(lambda template: len(template.product_variant_ids) > 1):

            for product_id in tmpl_id.product_variant_ids:
                default_code = code[tmpl_id.id]
                for att in product_id.attribute_line_ids.sorted(key=lambda r: r.attribute_id.sequence):
                    seq = product_id.attribute_value_ids.filtered(lambda r: r.attribute_id == att.attribute_id)
                    default_code += '.%s'%seq.code
                product_id.default_code = default_code

        for tmpl_id in self.with_context(active_test=False). \
                filtered(lambda template: len(template.product_variant_ids) == 1):
            tmpl_id.default_code = code[tmpl_id.id]

        return res





