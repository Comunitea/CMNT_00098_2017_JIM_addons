# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
# custom ftp lib helper
from ..base import ftp
# lib copied from odoo 11
from ..base import pycompat

base_product_publish_error = _('Error! You can not publish this product because ')
image_without_file_error = _('Error! Can not save an image without media file!')

####################### IMÁGENES PÚBLICAS #######################

class PublicImage:

	_max_public_file_size = (1920, None)
	_attr_public_file_name = 'public_file_name'

	@api.multi
	def _ftp_save_base64(self, base64_str):
		self._ftp_delete_file()
		return ftp.save_base64(base64_str)

	@api.multi
	def _ftp_delete_file(self):
		for record in self:
			# Delete old image
			if hasattr(record, self._attr_public_file_name) and getattr(record, self._attr_public_file_name):
				file_name = getattr(record, self._attr_public_file_name)
				ftp.delete_file(file_name)
		return False

	def _resize_large_image(self, base64_str=None):
		if base64_str:
			base64_source = base64_str.encode('ascii') if isinstance(base64_str, pycompat.text_type) else base64_str
			return tools.image_resize_image(base64_source, size=self._max_public_file_size)

####################### PRODUCTO #######################

class ProductTemplate(models.Model, PublicImage):
	_inherit = "product.template"

	website_published = fields.Boolean('Visible on Website', default=False, copy=False)
	public_categ_ids = fields.Many2many('product.public.category', string='Website Product Category', help="Categories for stores that sell to the end customer")
	product_image_ids = fields.One2many('product.image', 'product_tmpl_id', string='Images')
	public_file_name = fields.Char('Product Public File Name')

	@api.multi
	def website_publish_button(self):
		for product in self:
			if not product.website_published:
				if not self.tag_ids:
					raise ValidationError(_(base_product_publish_error + _('does not have tags.')))
				if not self.public_categ_ids:
					raise ValidationError(_(base_product_publish_error + _('does not have web categories.')))
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

	@api.model
	def create(self, vals):
		if vals.get('image_medium'):
			vals.update({ 'image_medium': self._resize_large_image(vals['image_medium']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image_medium']) })
		return super(ProductTemplate, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('image_medium') == False:
			self._ftp_delete_file()
			vals.update({ 'public_file_name': None })
		elif vals.get('image_medium'):
			vals.update({ 'image_medium': self._resize_large_image(vals['image_medium']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image_medium']) })
		return super(ProductTemplate, self).write(vals)

	@api.multi
	def unlink(self):
		for record in self:
			template_id = record.id
			default_image = record.public_file_name
			if super(ProductTemplate, record).unlink():
				ftp.delete_file(default_image)
				# Delete images with product_tmpl_id = null
				self.env['product.image'].search([('product_tmpl_id', '=', False)]).unlink()

####################### VARIANTE #######################

class ProductProduct(models.Model):
	_inherit = "product.product"

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

	image_variant = fields.Binary(compute='_compute_variant_images', store=False)
	product_image_ids = fields.One2many('product.image', string='Images', compute='_filter_variant_images')
	website_published = fields.Boolean('Visible on Website', default=False, copy=False)

	@api.multi
	def website_publish_button(self):
		for variant in self:
			if not variant.product_tmpl_id.website_published:
				raise ValidationError(_(base_product_publish_error + _('template is unpublished.')))
			variant.website_published = not variant.website_published

	@api.model
	def create(self, vals):
		template = self.env['product.template'].browse(vals.get('product_tmpl_id', 0))
		vals.update({ 'website_published': template.website_published })
		return super(ProductProduct, self).create(vals)

	@api.multi
	def unlink(self):
		for record in self:
			linked_images_ids = self.product_image_ids.ids
			if super(ProductProduct, record).unlink():
				self.env['product.image'].search([('id', 'in', linked_images_ids)]).unlink()

####################### MARCA #######################

class ProductBrand(models.Model, PublicImage):
	_inherit = "product.brand"
	_max_public_file_size = (600, None)
	public_file_name = fields.Char('Brand Public File Name')

	@api.model
	def create(self, vals):
		if vals.get('logo'):
			vals.update({ 'logo': self._resize_large_image(vals['logo']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['logo']) })
		return super(ProductBrand, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('logo') == False:
			self._ftp_delete_file()
			vals.update({ 'public_file_name': None })
		elif vals.get('logo'):
			vals.update({ 'logo': self._resize_large_image(vals['logo']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['logo']) })
		return super(ProductBrand, self).write(vals)

	@api.multi
	def unlink(self):
		for record in self:
			image_name = record.public_file_name
			if super(ProductBrand, record).unlink():
				ftp.delete_file(image_name)

####################### ETIQUETA (CATEGORÍA) #######################

class ProductTag(models.Model, PublicImage):
	_inherit = "product.tag"
	_order = "sequence, parent_id"

	_max_public_file_size = (1280, None)

	sequence = fields.Integer(help="Gives the sequence order for tags")
	public_file_name = fields.Char('Tag Public File Name')

	@api.model
	def create(self, vals):
		if vals.get('image'):
			vals.update({ 'image': self._resize_large_image(vals['image']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image']) })
		return super(ProductTag, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('image') == False:
			self._ftp_delete_file()
			vals.update({ 'public_file_name': None })
		elif vals.get('image'):
			vals.update({ 'image': self._resize_large_image(vals['image']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image']) })
		return super(ProductTag, self).write(vals)

	@api.multi
	def unlink(self):
		for record in self:
			image_name = record.public_file_name
			if super(ProductTag, record).unlink():
				ftp.delete_file(image_name)

####################### CATEGORÍA WEB #######################

class ProductPublicCategory(models.Model, PublicImage):
	_name = "product.public.category"
	_description = "Website Product Category"
	_order = "sequence, parent_id"

	_max_public_file_size = (1280, None)

	name = fields.Char(required=True, translate=True)
	parent_id = fields.Many2one('product.public.category', string='Parent Category', index=True)
	child_id = fields.One2many('product.public.category', 'parent_id', string='Children Categories')
	sequence = fields.Integer(help="Gives the sequence order when displaying a list of product categories.")
	image = fields.Binary(attachment=True, help="This field holds the image used as image for the category, limited to 1280px.")
	public_file_name = fields.Char('Category Public File Name')

	@api.model
	def create(self, vals):
		if vals.get('image'):
			vals.update({ 'image': self._resize_large_image(vals['image']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image']) })
		return super(ProductPublicCategory, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('image') == False:
			self._ftp_delete_file()
			vals.update({ 'public_file_name': None })
		elif vals.get('image'):
			vals.update({ 'image': self._resize_large_image(vals['image']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image']) })
		return super(ProductPublicCategory, self).write(vals)

	@api.multi
	def unlink(self):
		for record in self:
			image_name = record.public_file_name
			if super(ProductPublicCategory, record).unlink():
				ftp.delete_file(image_name)

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

####################### IMÁGENES DE PRODUCTO #######################

class ProductImage(models.Model, PublicImage):
	_name = "product.image"
	
	name = fields.Char('Name')
	image = fields.Binary('Image', attachment=True, required=True)
	public_file_name = fields.Char('Variant Image Public File Name')
	product_tmpl_id = fields.Many2one('product.template', string='Related Product', copy=True)
	product_attributes_values = fields.Many2many('product.attribute.value', relation='product_image_rel')

	@api.onchange('product_tmpl_id', 'product_attributes_values')
	def _onchange_product_attributes_values(self):
		product_attributes_values_ids = set(self.product_tmpl_id.attribute_line_ids.mapped('value_ids').ids)
		exclude_attributes_ids = set(self.product_attributes_values.mapped('attribute_id.value_ids').ids)
		attributes_values_ids = list(product_attributes_values_ids - exclude_attributes_ids)
		return { 
			'domain': {
				'product_attributes_values': [('id', 'in', attributes_values_ids)]
			}
		}

	@api.model
	def create(self, vals):
		if not vals.get('image'):
			raise ValidationError(image_without_file_error)
		else:
			vals.update({ 'image': self._resize_large_image(vals['image']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image']) })

		return super(ProductImage, self).create(vals)

	@api.multi
	def write(self, vals):
		if not vals.get('image', self.image):
			raise ValidationError(image_without_file_error)

		if vals.get('image'):
			vals.update({ 'image': self._resize_large_image(vals['image']) })
			vals.update({ 'public_file_name': self._ftp_save_base64(vals['image']) })

		return super(ProductImage, self).write(vals)

	@api.multi
	def unlink(self):
		for record in self:
			image_name = record.public_file_name
			if super(ProductImage, record).unlink():
				ftp.delete_file(image_name)