# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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

    @api.multi
    def write(self, vals):
        # Comprobamos si hay movimientos.
        if vals.get('default_code', False):
            for product in self:
                if product.stock_move_ids:
                    raise ValidationError(_("You can change code because this "
                                            "product has moves"))
        return super(ProductProduct, self).write(vals)


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    template_code = fields.Char("Template code", size=45, copy=False)

    @api.onchange('default_code')
    def onchange_default_code(self):
        self.template_code = self.default_code

    @api.multi
    def write(self, vals):
        # Si viene en el vals, actualizamos el template_code
        if vals.get('default_code', False):
            vals['template_code'] = vals.get('default_code', False)
        return super(ProductTemplate, self).write(vals)

    def set_product_product_default_code(self):
        for tmpl_id in self.with_context(active_test=False).\
                filtered(lambda x: len(x.product_variant_ids) > 1):
            for product_id in tmpl_id.product_variant_ids:
                default_code = tmpl_id.template_code
                for att in product_id.attribute_line_ids.\
                        sorted(key=lambda r: r.attribute_id.sequence):
                    seq = product_id.attribute_value_ids.\
                        filtered(lambda r: r.attribute_id == att.attribute_id)
                    default_code += '.%s' % seq.code
                    print default_code
                product_id.default_code = default_code

        for tmpl_id in self.with_context(active_test=False). \
                filtered(lambda x: len(x.product_variant_ids) == 1):
            tmpl_id.product_variant_ids[0].default_code = tmpl_id.template_code

    @api.multi
    def create_variant_ids(self):
        res = super(ProductTemplate, self).create_variant_ids()
        self.set_product_product_default_code()
        return res

    # Aqui sobre escribo directamente la función porque es más rápido
    # La función original distingue entre productos con variantes y sin.

    # @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    # def _compute_default_code(self):
    #     unique_variants = self.\
    #         filtered(lambda template: len(template.product_variant_ids) == 1)
    #     for template in unique_variants:
    #         template.default_code = template.product_variant_ids.default_code
    #     for template in (self - unique_variants):
    #         template.default_code = ''

    # Creo que en este caso, si tiene variantes, el default_code puede ser la
    # raiz del default_code del las variantes. Creo que vale así:

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        for template in self:
            template.default_code = template.template_code or ''

    @api.one
    def _set_default_code(self):
        self.template_code = self.default_code
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.default_code = self.default_code
        else:
            self.set_product_product_default_code()
