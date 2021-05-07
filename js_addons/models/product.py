# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from volumes import calcCubeVolume

class ProductTemplate(models.Model):
    _inherit = "product.template"

    discontinued_product = fields.Boolean('Discontinued', default=False, help="If checked, the product will not be sold in main company")
    product_size_width = fields.Float('Width', compute='_compute_size', inverse='_set_size', store=True, help="Product max width in cm")
    product_size_height = fields.Float('Height', compute='_compute_size', inverse='_set_size', store=True, help="Product max height in cm")
    product_size_depth = fields.Float('Depth', compute='_compute_size', inverse='_set_size', store=True, help="Product max depth in cm")
    volume = fields.Float(compute='_compute_size', inverse=False, digits=(3,6), store=False, help="Computed volume of the product (cube formula) in m³")

    # Sobreescribir product_custom por indicaciones de Comunitea
    name = fields.Char(translate=True)
    # description = fields.Text(translate=True)
    list_price = fields.Float(default=0.0)

    # Copiado de addons/product/models/product_template.py
    @api.depends('product_variant_ids', 'product_variant_ids.product_size_width', 'product_variant_ids.product_size_height', 'product_variant_ids.product_size_depth')
    def _compute_size(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.product_size_width = template.product_variant_ids.product_size_width
            template.product_size_height = template.product_variant_ids.product_size_height
            template.product_size_depth = template.product_variant_ids.product_size_depth
            template.volume = template.product_variant_ids.volume
        for template in (self - unique_variants):
            template.product_size_width = 0.0
            template.product_size_height = 0.0
            template.product_size_depth = 0.0
            template.volume = 0.0

    @api.one
    def _set_size(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_id.write({
                'product_size_width': self.product_size_width,
                'product_size_height': self.product_size_height,
                'product_size_depth': self.product_size_depth
            })

    @api.multi
    def _set_variant_discontinued(self, values):
        if 'discontinued_product' in values:
            for record in self:
                for variant in record.product_variant_ids:
                    variant.discontinued_product = values['discontinued_product']

    @api.model
    def create(self, vals):
        template = super(ProductTemplate, self).create(vals)
        template._set_variant_discontinued(vals);
        return template

    @api.multi
    def write(self, vals):
        self._set_variant_discontinued(vals);
        return super(ProductTemplate, self).write(vals)

    @api.model
    def ts_get_grid_structure(self, template_id, partner_id, pricelist_id):
        # Esta función se llama desde televenta cuando se añade un producto con variantes
        # modificamos el diccionario que devuelve para añadirle el campo descatalogado
        template = self.browse(template_id)
        result = super(ProductTemplate, self).ts_get_grid_structure(template_id, partner_id, pricelist_id)

        if len(result['str_table']):
            for x in result['str_table']:
                if len(result['str_table'][x]):
                    for y in result['str_table'][x]:
                        values = self.env['product.attribute.value'].browse(x)
                        if y: values += self.env['product.attribute.value'].browse(y)

                        product = template.product_variant_ids.filtered(lambda x: not(values - x.attribute_value_ids))[:1]

                        result['str_table'][x][y].update({
                            'discontinued': product and product.discontinued_product or False
                        })

        return result

class ProductProduct(models.Model):
    _inherit = "product.product"

    discontinued_product = fields.Boolean('Discontinued', default=False, help="If checked, the variant will not be sold in main company")
    product_size_width = fields.Float('Width', help="Product max width in cm")
    product_size_height = fields.Float('Height', help="Product max height in cm")
    product_size_depth = fields.Float('Depth', help="Product max depth in cm")
    volume = fields.Float(compute='_compute_volume', digits=(3,6), store=False, help="Computed volume of the product (cube formula) in m³")

    @api.depends('product_size_depth', 'product_size_width', 'product_size_height')
    def _compute_volume(self):
        for record in self:
            volumeInCm = calcCubeVolume(record.product_size_width, record.product_size_height, record.product_size_depth)
            record.volume = volumeInCm / 1000000
