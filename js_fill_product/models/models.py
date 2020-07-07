# -*- coding: utf-8 -*-
# © 2018 Miguel Ángel García <info@miguel-angel-garcia.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
import urllib2 as urllib
import base64

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	@api.multi
	def js_download_images(self):
		for record in self:
			with api.Environment.manage():
				with self.pool.cursor() as new_cr:
					irecord = record.with_env(self.env(cr=new_cr))

					# Comprobamos que el producto tenga asignado código
					if irecord.default_code == False or irecord.default_code == None or irecord.default_code == '':
						return False

					print("################ DESCARGANDO IMAGEN (PRODUCTO)")

					# URL de las imágenes
					URL = "http://resources.jimsports.website/Intranet/images/"
					# Eliminamos espacios de inicio y final de la referencia y cogemos la primera parte si tiene puntos
					product_reference = irecord.default_code.strip().rsplit('.')[0]
					# Nombre del fichero
					image_path = '%s%s.jpg' % (URL, product_reference)

					# Carga la imagen principal
					try:
						print(image_path)
						image = urllib.urlopen(image_path).read()
						imageBase64 = base64.b64encode(image)
					except Exception as e:
						print("ERROR en la descarga de la imagen: ", e.reason)
						return False

					# Guarda la transacción y descarga las de las variantes
					try:
						irecord.with_context(resize_img=False).write({ 'image_medium':imageBase64 })
						new_cr.commit()
						irecord.product_variant_ids.js_download_images()
					except Exception:
						new_cr.rollback()

class ProductProduct(models.Model):
	_inherit = 'product.product'

	@api.multi
	def js_download_images(self):
		for record in self:
			with api.Environment.manage():
				with self.pool.cursor() as new_cr:
					irecord = record.with_env(self.env(cr=new_cr))

					# Comprobamos que el producto tenga asignado código
					if irecord.default_code == False or irecord.default_code == None or irecord.default_code == '':
						return False

					print("################ DESCARGANDO IMÁGENES (VARIANTE)")

					# Eliminar imágenes antiguas
					irecord.product_image_ids.unlink()

					# Carga las imágenes secundarias
					i = 1
					
					# Bucle para generar las combinaciones de nombres
					while True:
						image_name = '%s-%s' % (irecord.default_code, i)
						image_path = '%s%s.jpg' % (URL, image_name)

						try:
							print(image_path)
							image = urllib.urlopen(image_path).read()
							imageBase64 = base64.b64encode(image)
						except Exception as e:
							print("ERROR en la descarga de la imagen %s: " % image_path, e.reason)
							return True
						finally:
							i += 1

					# Guarda la transacción y descarga las de las variantes
					try:
						new_image = self.env['product.image'].with_context(resize_img=False).create({ 
							'product_tmpl_id': irecord.id, 
							'name': irecord.name, 
							'image': imageBase64 
						})
						new_cr.commit()
					except Exception:
						new_cr.rollback()