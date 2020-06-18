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

        # Comprobamos que el producto tenga asignado código
        if self.default_code == False or self.default_code == None or self.default_code == '':
            return(False)

        # URL de las imágenes
        URL = "http://resources.jimsports.website/Intranet/images/"
        # Eliminamos espacios de inicio y final de la referencia y cogemos la primera parte si tiene puntos
        product_reference = self.default_code.strip().rsplit('.')[0]
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
        self.write({ 'image_medium':imageBase64 }, resize=False)

        print("################ DESCARGANDO IMAGENES (VARIANTES)")
        # Eliminar imágenes antiguas
        self.product_image_ids.unlink()

        # Carga las imágenes secundarias
        i = 1
        # Bucle para generar las combinaciones de nombres
        while True:
            image_name = self.default_code + '-' + str(i)
            try:
                print(URL + image_name)
                image = urllib.urlopen(URL + image_name + ".jpg").read()
                imageBase64 = base64.b64encode(image)
            except urllib.URLError as e:
                    return(True)
            new_image = self.env['product.image'].create({'product_tmpl_id': self.id, 'name': self.name, 'image': imageBase64}, resize=False)
            i += 1

    @api.model
    def batch_update(self, test_limit=None):
        print('[js_fill_product] ****** Inicio del proceso de descarga de imágenes ******')

        product_list = self.search([('sale_ok', '=', True),
                                        ('default_code', '!=', False),
                                        ('type', '=', 'product')],
                                        order='id', limit=test_limit)

        debug_total = str(len(product_list))
        
        print('[js_fill_product] Se recorrerán {} productos'.format(debug_total))

        for product in product_list:
            if product.js_download_images():
                print('[js_fill_product] Descargadas las imágenes de {}'.format(product.default_code))

        print('[js_fill_product] ****** Fin del proceso de descarga de imágenes ******')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.one
    def js_download_images(self):
        # Llamamos a la función del template para que no dé error desde product.product
        self.product_tmpl_id.js_download_images()