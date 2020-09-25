# -*- coding: utf-8 -*-
# © 2018 Miguel Ángel García <info@miguel-angel-garcia.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
import requests
import base64

from time import sleep

# URL de las imágenes
URL = 'http://192.168.1.199/Intranet/images/'

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	@api.model
	def __get_image(self, route, only_check=False):
		try:
			response = requests.get(route, stream=True)
		except Exception as e:
			print("ERROR [%s]" % route, e)
			return False
		else:
			if response.status_code == 200:
				if only_check:
					return True
				return base64.b64encode(response.content)
		print("NOT FOUND [%s]!" % route, response.status_code)
		return False

	@api.multi
	def js_download_images(self, images_url=URL, resize=False):
		img = None
		self.ensure_one()
		filename = getattr(self, self._attr_public_file_name)

		with api.Environment.manage():
			with self.pool.cursor() as new_cr:
				irecord = self.with_env(self.env(cr=new_cr))
				
				# Comprobamos que el producto tenga asignado código
				if irecord.default_code == False or irecord.default_code == None or irecord.default_code == '':
					return False

				product_reference = irecord.default_code.strip().rsplit('.')[0]

				# Nombre del fichero
				image_path = '%s%s.jpg' % (URL, product_reference)
				imageBase64 = self.__get_image(image_path)

				if imageBase64:
					irecord.with_context(resize_img=resize).write({ 'image':imageBase64 })

				# Eliminar imágenes antiguas
				irecord.product_image_ids.unlink()

				# Tiene variantes
				if len(irecord.product_variant_ids) > 1:
					# Metemos de nuevo la imágen principal en la pestaña de imágenes
					# para poder asignarle un atributo para la web
					if imageBase64:
						new_image = irecord.env['product.image'].with_context(resize_img=resize).create({ 
							'product_tmpl_id': irecord.id, 
							'name': irecord.name, 
							'image': imageBase64 
						})

				# Carga las imágenes secundarias
				i = 1
				
				while True:
					image_name = '%s-%s' % (product_reference, i)
					image_path = '%s%s.jpg' % (URL, image_name)
					imageBase64 = self.__get_image(image_path)

					if imageBase64:
						new_image = irecord.env['product.image'].with_context(resize_img=resize).create({ 
							'product_tmpl_id': irecord.id, 
							'name': irecord.name, 
							'image': imageBase64 
						})
					else:
						return True

					i += 1

				try:
					new_cr.commit()
				except:
					new_cr.rollback()

		return True

class ProductProduct(models.Model):
	_inherit = 'product.product'

	@api.multi
	def js_download_images(self):
		self.ensure_one()
		# Llamamos a la función del template para que no dé error desde product.product
		self.product_tmpl_id.js_download_images()