# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

base_product_publish_error = 'Error! You can not publish this product because '

class ProductPublicCategory(models.Model):
	_name = "product.public.category"
	_description = "Website Product Category"
	_order = "sequence, name"

	name = fields.Char(required=True, translate=True)
	parent_id = fields.Many2one('product.public.category', string='Parent Category', index=True)
	child_id = fields.One2many('product.public.category', 'parent_id', string='Children Categories')
	sequence = fields.Integer(help="Gives the sequence order when displaying a list of product categories.")
	image = fields.Binary(attachment=True, help="This field holds the image used as image for the category, limited to 1024x1024px.")

	@api.model
	def create(self, vals):
		tools.image_resize_images(vals)
		return super(ProductPublicCategory, self).create(vals)

	@api.multi
	def write(self, vals):
		tools.image_resize_images(vals)
		return super(ProductPublicCategory, self).write(vals)

	@api.constrains('parent_id')
	def check_parent_id(self):
		if not self._check_recursion():
			raise ValueError(_('Error! You cannot create recursive categories.'))

	@api.multi
	def name_get(self):
		res = []
		for category in self:
			names = [category.name]
			parent_category = category.parent_id
			while parent_category:
				names.append(parent_category.name)
				parent_category = parent_category.parent_id
			res.append((category.id, ' / '.join(reversed(names))))
		return res

class ProductTemplate(models.Model):
	_inherit = ["product.template"]

	website_published = fields.Boolean('Visible on Website', default=False, copy=False)
	public_categ_ids = fields.Many2many('product.public.category', string='Website Product Category', help="Categories for stores that sell to the end customer")

	@api.multi
	def website_publish_button(self):
		for product in self:
			if not product.website_published:
				if not self.tag_ids:
					raise ValidationError(_(base_product_publish_error + 'does not have tags.'))
				if not self.public_categ_ids:
					raise ValidationError(_(base_product_publish_error + 'does not have web categories.'))
			toggled_status = bool(not product.website_published)
			product.website_published = toggled_status
			product.mapped('product_variant_ids').write({ 'website_published': toggled_status })

	@api.multi
	def create_variant_ids(self):
		res = super(ProductTemplate, self).create_variant_ids()
		# Publish new variants based on template
		for tmpl_id in self.with_context(active_test=False).filtered(lambda x: x.attribute_line_ids):
			for product_id in tmpl_id.product_variant_ids:
				website_published = tmpl_id.website_published
				if product_id.website_published != website_published:
					product_id.website_published = website_published
		# Unpublish unique variant without attributes
		for tmpl_id in self.with_context(active_test=False).filtered(lambda x: len(x.product_variant_ids) == 1 and not x.attribute_line_ids):
			if tmpl_id.product_variant_ids[0].website_published:
				tmpl_id.product_variant_ids[0].website_published = False
		return res

class ProductProduct(models.Model):
	_inherit = ["product.product"]

	website_published = fields.Boolean('Visible on Website', default=False, copy=False)

	@api.multi
	def website_publish_button(self):
		for variant in self:
			if not variant.product_tmpl_id.website_published:
				raise ValidationError(_(base_product_publish_error + 'template is unpublished.'))
			variant.website_published = not variant.website_published

	@api.model
	def create(self, vals):
		template = self.env['product.template'].browse(vals.get('product_tmpl_id', 0))
		vals.update({ 'website_published': template.website_published })
		return super(ProductProduct, self).create(vals)