# -*- coding: utf-8 -*-
# © 2018 Miguel Ángel García <info@miguel-angel-garcia.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
import urllib2 as urllib
import base64
from time import sleep

# URL de las imágenes
URL = 'http://192.168.1.199/Intranet/images/'

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	@api.multi
	def js_download_images(self, images_url=URL, resize=False):
		img = None
		self.ensure_one()
		base_url = 'https://b2b.grupojimsports.com/images/' # self.env['b2b.settings'].get_param('base_url')
		filename = getattr(self, self._attr_public_file_name)

		if filename:
			try:
				fileuri = base_url + filename
				print("# BUSCANDO IMAGEN %s" % fileuri)
				img = urllib.urlopen(fileuri)
			except:
				print("# IMAGEN ANTIGUA NO ENCONTRADA!", filename)
				img = None
		else:
			print("# SIN IMAGEN GUARDADA!")

		if not img or img.code != 200:

			with api.Environment.manage():
				with self.pool.cursor() as new_cr:
					irecord = self.with_env(self.env(cr=new_cr))
					
					# Comprobamos que el producto tenga asignado código
					if irecord.default_code == False or irecord.default_code == None or irecord.default_code == '':
						return False

					product_reference = irecord.default_code.strip().rsplit('.')[0]
					print("# DESCARGANDO IMAGEN (PRODUCTO)", product_reference)

					# Nombre del fichero
					image_path = '%s%s.jpg' % (URL, product_reference)

					try:
						image = urllib.urlopen(image_path).read()
						imageBase64 = base64.b64encode(image)
						irecord.with_context(resize_img=resize).write({ 'image':imageBase64 })
					except urllib.URLError as e:
						print("ERROR [%s]" % image_path, e.reason)
						return False

					print("# DESCARGANDO IMAGENES (VARIANTE)", irecord.default_code)

					# Eliminar imágenes antiguas
					irecord.product_image_ids.unlink()

					# Carga las imágenes secundarias
					i = 1
					
					while True:
						image_name = '%s-%s' % (product_reference, i)
						image_path = '%s%s.jpg' % (URL, image_name)

						try:
							image = urllib.urlopen(image_path).read()
							imageBase64 = base64.b64encode(image)
							new_image = irecord.env['product.image'].with_context(resize_img=resize).create({ 
								'product_tmpl_id': irecord.id, 
								'name': irecord.name, 
								'image': imageBase64 
							})
						except urllib.URLError as e:
							print("ERROR [%s]" % image_path, e.reason)
							return True
						finally:
							i += 1

					try:
						new_cr.commit()
					except:
						new_cr.rollback()
					finally:
						sleep(2)

		else:
			print("# IMAGEN OK!!!")

		return True

class ProductProduct(models.Model):
	_inherit = 'product.product'

	@api.multi
	def js_download_images(self):
		self.ensure_one()
		# Llamamos a la función del template para que no dé error desde product.product
		self.product_tmpl_id.js_download_images()