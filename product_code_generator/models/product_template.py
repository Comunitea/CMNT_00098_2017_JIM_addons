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

    code = fields.Char("Code", help="Code number for this variant",
                       required=True)
    is_color = fields.Boolean("Represents a color",
                              related="attribute_id.is_color")
    sequence = fields.Integer('Sequence', help="Determine the display order", readonly=True, default = 0)

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
        if vals.get('default_code', False) and False:
            for product in self:
                if product.stock_move_ids:
                    raise ValidationError(_("You can change code because this "
                                            "product has moves"))
        return super(ProductProduct, self).write(vals)

    @api.model
    def create(self, vals):
        product = super(ProductProduct, self).create(vals)
        if vals.get('default_code', False):
            if not product.product_tmpl_id.default_code:
                product.product_tmpl_id.default_code = vals['default_code']
        return product


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    template_code = fields.Char("Template code", size=45, copy=False)

    def set_product_product_default_code(self):
        for tmpl_id in self.with_context(active_test=False).\
                filtered(lambda x: x.attribute_line_ids):
            for product_id in tmpl_id.product_variant_ids:
                default_code = tmpl_id.template_code
                for att in product_id.attribute_line_ids.\
                        sorted(key=lambda r: r.attribute_id.sequence):
                    seq = product_id.attribute_value_ids.\
                        filtered(lambda r: r.attribute_id == att.attribute_id)
                    seq_code = seq.code
                    default_code += '.%s' %seq_code
                product_id.default_code = default_code

        for tmpl_id in self.with_context(active_test=False). \
                filtered(lambda x: len(x.product_variant_ids) == 1 and not
                         x.attribute_line_ids):
            tmpl_id.product_variant_ids[0].default_code = tmpl_id.template_code

    @api.multi
    def create_variant_ids(self):
        res = super(ProductTemplate, self).create_variant_ids()
        self.set_product_product_default_code()
        return res

    @api.depends('template_code')
    def _compute_default_code(self):
        for template in self:
            template.default_code = template.template_code or ''

    @api.one
    def _set_default_code(self):
        self.template_code = self.default_code
        if self.product_variant_ids:
            if len(self.product_variant_ids) == 1 and not \
                    self.attribute_line_ids:
                self.product_variant_ids.default_code = self.default_code
            else:
                self.set_product_product_default_code()
