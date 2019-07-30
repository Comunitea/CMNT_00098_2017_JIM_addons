# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    discontinued_product = fields.Boolean('Discontinued', default=False, help="If checked, the product will not be sold in main company")
    product_size_width = fields.Float('Width', help="Max width of the product in cm")
    product_size_height = fields.Float('Height', help="Max height of the product in cm")
    product_size_depth = fields.Float('Depth', help="Max depth of the product in cm")
    volume = fields.Float(compute='_compute_volume', digits=(3,2), store=False, help="Computed volume of the product (cube formula) in m³")

    #override
    @api.onchange('product_size_depth', 'product_size_width', 'product_size_height')
    def _compute_volume(self):
        for record in self:
            record.volume = 0.0
            if  record.product_size_width and record.product_size_height and record.product_size_depth:
                record.volume = float(record.product_size_width * record.product_size_height * record.product_size_depth) / 100

    def _set_variant_discontinued(self, values):
        if 'discontinued_product' in values:
            for variant in self.product_variant_ids:
                variant.discontinued_product = values['discontinued_product']

    @api.model
    def create(self, vals):
        self._set_variant_discontinued(vals);
        template = super(ProductTemplate, self).create(vals)
        related_vals = {}
        if vals.get('product_size_width'):
            related_vals['product_size_width'] = vals['product_size_width']
        if vals.get('product_size_height'):
            related_vals['product_size_height'] = vals['product_size_height']
        if vals.get('product_size_depth'):
            related_vals['product_size_depth'] = vals['product_size_depth']
        if related_vals:
            template.write(related_vals)
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
                            'discontinued': product and product.discontinued_product or False,
                        })

        return result

class ProductProduct(models.Model):
    _inherit = "product.product"

    discontinued_product = fields.Boolean('Discontinued', default=False, help="If checked, the variant will not be sold in main company")
    product_size_width = fields.Float('Width', help="Max width of the product in cm")
    product_size_height = fields.Float('Height', help="Max height of the product in cm")
    product_size_depth = fields.Float('Depth', help="Max depth of the product in cm")
    volume = fields.Float(compute='_compute_volume', digits=(3,2), store=False, help="Computed volume of the product (cube formula) in m³")

    @api.onchange('product_size_depth', 'product_size_width', 'product_size_height')
    def _compute_volume(self):
        for record in self:
            record.volume = 0.0
            if  record.product_size_width and record.product_size_height and record.product_size_depth:
                record.volume = float(record.product_size_width * record.product_size_height * record.product_size_depth) / 100
