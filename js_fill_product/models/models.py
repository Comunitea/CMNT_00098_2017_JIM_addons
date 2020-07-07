# -*- coding: utf-8 -*-
# © 2018 Miguel Ángel García <info@miguel-angel-garcia.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
import urllib2 as urllib
import base64

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Descarga las imágenes para el producto desde el servidor de Jim Sports
    @api.one
    def js_download_images(self):

        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                # Autocommit ON
                new_cr.autocommit(True)
                # Fresh record
                record_issolated = self.with_env(self.env(cr=new_cr))

                # Comprobamos que el producto tenga asignado código
                if record_issolated.default_code == False or record_issolated.default_code == None or record_issolated.default_code == '':
                    return(False)

                # URL de las imágenes
                URL = "http://resources.jimsports.website/Intranet/images/"
                # Eliminamos espacios de inicio y final de la referencia y cogemos la primera parte si tiene puntos
                product_reference = record_issolated.default_code.strip().rsplit('.')[0]
                # Nombre del fichero
                image_name = product_reference + ".jpg"

                print("################ DESCARGANDO IMAGEN (PRINCIPAL)")
                # Carga la imagen principal
                try:
                    print(URL + image_name)
                    image = urllib.urlopen(URL + image_name).read()
                except urllib.URLError as e:
                    print("ERROR en la descarga de la imagen: ", e.reason)
                    return(False)
                imageBase64 = base64.b64encode(image)
                record_issolated.with_context(resize_img=False).write({ 'image_medium':imageBase64 })

                print("################ DESCARGANDO IMAGENES (VARIANTES)")
                # Eliminar imágenes antiguas
                record_issolated.product_image_ids.unlink()

                # Carga las imágenes secundarias
                i = 1
                # Bucle para generar las combinaciones de nombres
                while True:
                    image_name = record_issolated.default_code + '-' + str(i)
                    try:
                        print(URL + image_name)
                        image = urllib.urlopen(URL + image_name + ".jpg").read()
                        imageBase64 = base64.b64encode(image)
                    except urllib.URLError as e:
                            return(True)
                    new_image = record_issolated.env['product.image'].with_context(resize_img=False).create({'product_tmpl_id': self.id, 'name': self.name, 'image': imageBase64})
                    i += 1

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.one
    def js_download_images(self):
        # Llamamos a la función del template para que no dé error desde product.product
        self.product_tmpl_id.js_download_images()