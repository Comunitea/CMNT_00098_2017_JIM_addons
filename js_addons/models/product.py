# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    discontinued_product = fields.Boolean('Discontinued', default=False, help="If checked, the product will not be sold in main company")

    def _set_variant_discontinued(self, values):
        if 'discontinued_product' in values:
            for variant in self.product_variant_ids:
                variant.discontinued_product = values['discontinued_product']

    @api.model
    def create(self, vals):
        self._set_variant_discontinued(vals);
        return super(ProductTemplate, self).create(vals)

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
