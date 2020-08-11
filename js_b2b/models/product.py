# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
# custom ftp lib helper
from ..base import ftp
# lib copied from odoo 11
from ..base import pycompat
# barcode validation
import barcodenumber

base_product_publish_error = _('Error! You can not publish this product because ')
image_without_file_error = _('Error! Can not save an image without media file!')

####################### IMÁGENES PÚBLICAS #######################
# Esta clase permite simplificar mucho los modelos de las imágenes que se quieren subir al FTP
# Ya que nos evita tener que sobreescribir el create, write y unlink con el mismo código
# Para usarla haremos una herencia múltiple Ej. ["product.template", "b2b.image"]

class PublicImage(models.AbstractModel):
	_name = "b2b.image"

	_max_public_file_size = (1920, None)
	_attr_image_model_field = 'image'
	_attr_public_file_name = 'public_image_name'

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

	@api.model
	def create(self, vals):
		resize = self.env.context.get('resize_img', True)

		try:
			if vals.get(self._attr_image_model_field):
				img = self._resize_large_image(vals[self._attr_image_model_field]) if resize else vals[self._attr_image_model_field]
				vals.update({ self._attr_image_model_field: img, self._attr_public_file_name: self._ftp_save_base64(img) })
			return super(PublicImage, self).create(vals)
		except:
			self._ftp_delete_file()
			return False

	@api.multi
	def write(self, vals):
		resize = self.env.context.get('resize_img', True)
		new_image_name = None

		try:
			if vals.get(self._attr_image_model_field) == False:
				self._ftp_delete_file()
				vals.update({ self._attr_public_file_name: None })
			elif vals.get(self._attr_image_model_field):
				img = self._resize_large_image(vals[self._attr_image_model_field]) if resize else vals[self._attr_image_model_field]
				new_image_name = self._ftp_save_base64(img) 
				vals.update({ self._attr_image_model_field: img, self._attr_public_file_name: new_image_name })
			return super(PublicImage, self).write(vals)
		except:
			ftp.delete_file(new_image_name)
			return False


	@api.multi
	def unlink(self):
		for record in self:
			record_image_name = getattr(record, self._attr_public_file_name)
			if super(PublicImage, record).unlink():
				ftp.delete_file(record_image_name)
		return True

####################### PRODUCTO #######################

class ProductTemplate(models.Model):
	_name = "product.template"
	_inherit = ["product.template", "b2b.image"]

	# PublicImage params
	# _attr_image_model_field = 'image_medium'

	website_published = fields.Boolean('Visible on Website', default=False, copy=False)
	public_categ_ids = fields.Many2many('product.public.category', string='Website Product Category', help="Categories for stores that sells to end customer")
	product_image_ids = fields.One2many('product.image', 'product_tmpl_id', string='Images')
	public_image_name = fields.Char('Product Public Image Name')

	@api.multi
	def has_valid_barcode(self, code_type='ean13'):
		self.ensure_one()
		return barcodenumber.check_code(code_type, self.barcode)

	@api.multi
	def website_publish_button(self):
		self.ensure_one()

		if not self.id:
			raise ValidationError(_('Can not publish a product before saving it!'))

		self.website_published = not self.website_published

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

	@api.multi
	def write(self, vals):

		# Check if can be published
		if 'website_published' in vals:
			for product in self:
				if not product.website_published and vals['website_published']:
					if not product.tag_ids:
						raise ValidationError(_(base_product_publish_error) + _('does not have tags.'))
					if not product.public_categ_ids:
						raise ValidationError(_(base_product_publish_error) + _('does not have web categories.'))
					if product.barcode and not product.has_valid_barcode():
						raise ValidationError(_(base_product_publish_error) + _('does not have a valid barcode.'))
					if product.type != 'product':
						raise ValidationError(_(base_product_publish_error) + _('is not stockable.'))

		updated = super(ProductTemplate, self).write(vals)

		# Update website_published on variants
		if 'website_published' in vals:
			for product in self:
				# Publish variants
				product.mapped('product_variant_ids').write({ 'website_published': product.website_published })

	@api.multi
	def unlink(self):
		for record in self:
			default_image = record.public_image_name
			if super(ProductTemplate, record).unlink():
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
	def has_valid_barcode(self, code_type='ean13'):
		self.ensure_one()
		return barcodenumber.check_code(code_type, self.barcode)

	@api.multi
	def website_publish_button(self):
		self.ensure_one()

		if not self.id:
			raise ValidationError(_('Can not publish a variant before saving it!'))

		self.website_published = not self.website_published

	@api.model
	def create(self, vals):
		template = self.env['product.template'].browse(vals.get('product_tmpl_id', 0))
		vals.update({ 'website_published': template.website_published })
		return super(ProductProduct, self).create(vals)

	@api.multi
	def write(self, vals):

		# Check if can be published
		if 'website_published' in vals:
			for variant in self:
				if not variant.website_published and vals['website_published']:
					if not variant.product_tmpl_id.website_published:
						raise ValidationError(_(base_product_publish_error) + _('template is unpublished.'))
					if not variant.tag_ids:
						raise ValidationError(_(base_product_publish_error) + _('does not have tags.'))
					if variant.barcode and not variant.has_valid_barcode():
						raise ValidationError(_(base_product_publish_error) + _('does not have a valid barcode.'))
					if variant.type != 'product':
						raise ValidationError(_(base_product_publish_error) + _('is not stockable.'))

		return super(ProductProduct, self).write(vals)

	@api.multi
	def unlink(self):
		for record in self:
			linked_images_ids = self.product_image_ids.ids
			if super(ProductProduct, record).unlink():
				self.env['product.image'].search([('id', 'in', linked_images_ids)]).unlink()

####################### MARCA #######################

class ProductBrand(models.Model):
	_name = "product.brand"
	_inherit = ["product.brand", "b2b.image"]

	# PublicImage params
	_max_public_file_size = (600, None)
	_attr_image_model_field = 'logo'

	public_image_name = fields.Char('Brand Public File Name')

####################### ETIQUETA (CATEGORÍA) #######################

class ProductTag(models.Model):
	_name = "product.tag"
	_inherit = ["product.tag", "b2b.image"]
	_order = "parent_left, sequence"

	# PublicImage params
	_attr_image_model_field = 'image'
	_max_public_file_size = (1280, None)

	child_ids = fields.One2many(domain=['|', ('active', '=', True), ('active', '=', False)])
	sequence = fields.Integer(help="Gives the sequence order for tags")
	public_image_name = fields.Char('Tag Public File Name')

####################### ATRIBUTOS #######################

class ProductAttributeValue(models.Model):
	_name = "product.attribute.value"
	_inherit = ["product.attribute.value", "b2b.image"]

	# PublicImage params
	_attr_image_model_field = 'image_color'
	_max_public_file_size = (62, 62)

	is_color = fields.Boolean(related='attribute_id.is_color', store=False)
	html_color = fields.Char(string='HTML Color', oldname='color', help="Here you can set a specific HTML color index (e.g. #ff0000) to display the color on the website if the attibute type is 'Color'.")
	image_color = fields.Binary(attachment=True, help="This field holds the image used as thumbnail for the attribute colors, limited to 62px.")
	image_color_filename = fields.Char(string='Color Image Name') # To check extension
	public_image_name = fields.Char('Color Public File Name')

	@api.one
	@api.constrains('image_color_filename')
	def _check_filename(self):
		if self.image_color and self.image_color_filename:
			# Check the file's extension
			tmp = self.image_color_filename.split('.')
			ext = tmp[len(tmp)-1]
			if ext != 'jpg':
				raise ValidationError(_("The image must be a jpg file"))

####################### CATEGORÍA WEB #######################

class ProductPublicCategory(models.Model):
	_name = "product.public.category"
	_inherit = ["b2b.image"]
	_description = "Website Product Category"
	_order = "sequence, parent_id"

	# PublicImage params
	_max_public_file_size = (1280, None)

	name = fields.Char(required=True, translate=True)
	parent_id = fields.Many2one('product.public.category', string='Parent Category', index=True)
	child_id = fields.One2many('product.public.category', 'parent_id', string='Children Categories')
	sequence = fields.Integer(help="Gives the sequence order when displaying a list of product categories.")
	image = fields.Binary(attachment=True, help="This field holds the image used as image for the category, limited to 1280px.")
	public_image_name = fields.Char('Category Public File Name')

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

class ProductImage(models.Model):
	_name = "product.image"
	_inherit = ["b2b.image"]
	
	name = fields.Char('Name')
	image = fields.Binary('Image', attachment=True, required=True)
	public_image_name = fields.Char('Variant Image Public File Name')
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