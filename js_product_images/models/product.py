# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
# lib copied from odoo 11
from . import pycompat

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_image_ids = fields.One2many('product.image', 'product_tmpl_id', string='Images')

class Product(models.Model):
    _inherit = 'product.product'

    @api.one
    def _filter_variant_images(self):
        product_attrs = [attr.id for attr in self.attribute_value_ids]

        self.product_image_ids = self.env['product.image'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ]).filtered(lambda image: all(map(lambda x: x in product_attrs, image.product_attributes_values._ids)))
        # To exclude images without all attribute of variant use this line instead
        # filtered(lambda image: all(map(lambda x,y: x in product_attrs and y in image.product_attributes_values._ids, image.product_attributes_values._ids, product_attrs)))

    @api.one
    @api.depends('product_image_ids')
    def _compute_variant_images(self):
        if self.product_image_ids:
            self.image_variant = self.product_image_ids[0].image
        elif self.product_tmpl_id.image_medium:
            self.image_variant = self.product_tmpl_id.image_medium
        else:
            self.image_variant = False

    product_image_ids = fields.One2many('product.image', string='Images', compute='_filter_variant_images')
    image_variant = fields.Binary(compute='_compute_variant_images', store=False) # override

class ProductImage(models.Model):
    _name = 'product.image'

    @api.model
    def _filter_product_attributes(self):
        product_tmpl_id = self.env.context.get('default_product_tmpl_id')
        if product_tmpl_id:
            product_attributes = self.env['product.attribute.line'].search([('product_tmpl_id', '=', product_tmpl_id)])
            return [('id', 'in', [id for attr in product_attributes for id in attr.value_ids._ids])]
        else:
            return []

    name = fields.Char('Name', translate=True)
    image = fields.Binary('Image', attachment=True)
    product_tmpl_id = fields.Many2one('product.template', string='Related Product', ondelete='cascade', copy=True)
    product_attributes_values = fields.Many2many('product.attribute.value', relation='product_image_rel', domain=_filter_product_attributes)

    # override
    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(ProductImage, self).create(vals)

    # override
    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(ProductImage, self).write(vals)
