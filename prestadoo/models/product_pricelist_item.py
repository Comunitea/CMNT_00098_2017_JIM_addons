# -*- coding: utf-8 -*-
from odoo import api, models
from ..jesie import Jesie
from ..output_helper import OutputHelper as Console
from .. import tools


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    version = None
    row_insert_limit = 1000

    @api.model
    def prices_2_jesie(self):
        Console.debug('[Prestadoo] Inicio de proceso de notificación de PRICES a Jesie')

        self.version = tools.format_date(output_date_format='%Y%m%d%H%M%S')
        self.get_row_insert_limit()

        Jesie.delete_jesie_prices()

        self.pricelist_prices_2_jesie()
        self.customer_prices_2_jesie()
        self.launch_jesie_enqueue()

        Console.debug('[Prestadoo] Fin de proceso de notificación de PRICES a Jesie')

    def get_product_pricelist_query(self):
        param = self.env["ir.config_parameter"].search([('key', '=', 'prestadoo.product.pricelist.query')])

        if not param:
            Console.debug("[Prestadoo] No se ha encontrado parámetro 'prestadoo.product.pricelist.query' en "
                          "'Configuración -> Parámetros -> Parámetros del sistema'.")
            return False
        else:
            return param.value

    def get_customer_prices_query(self):
        param = self.env["ir.config_parameter"].search([('key', '=', 'prestadoo.customer.prices.query')])

        if not param:
            Console.debug("[Prestadoo] No se ha encontrado parámetro 'prestadoo.customer.prices.query' en "
                          "'Configuración -> Parámetros -> Parámetros del sistema'.")
            return False
        else:
            return param.value

    def get_row_insert_limit(self):
        # Tenemos que hacer inserciones en bloques de 1000 ya que es el máximo permitido. Para esto, utilizaremos
        # un parámetro de Odoo, así se podrá modificar el tamaño en caso de ser necesario.
        param = self.env["ir.config_parameter"].search([('key', '=', 'prestadoo.pricelist.insert.limit')])

        self.row_insert_limit = 1000

        if not param:
            self.row_insert_limit = 1000
            Console.debug(
                "[Prestadoo] No se ha encontrado parámetro 'prestadoo.pricelist.insert.limit' en "
                "'Configuración -> Parámetros -> Parámetros del sistema'; se utilizará 1000.")
        else:
            self.row_insert_limit = int(param.value)
            Console.debug("[Prestadoo] Encontrado parámetro 'prestadoo.pricelist.insert.limit'. "
                          "Valor = {}".format(param.value))

    def pricelist_prices_2_jesie(self):
        Console.debug('[Prestadoo] Obteniendo precios de listas de precios')

        sql_query = self.get_product_pricelist_query()

        if sql_query:
            self.env.cr.execute(sql_query)
            prices = self.env.cr.fetchall()

            Console.debug('[Prestadoo] Se van a volcar {} registros'.format(len(prices)))
            if prices:
                Jesie.insert_jesie_prices(prices, self.version, self.row_insert_limit)
            Console.debug('[Prestadoo] {} registros volcados'.format(len(prices)))

            Console.debug('[Prestadoo] FIN de proceso de volcado de precios de listas de precios')
        else:
            Console.debug('[Prestadoo] No existe la consulta')

    def customer_prices_2_jesie(self):
        Console.debug('[Prestadoo] Obteniendo precios específicos de clientes')

        sql_query = self.get_customer_prices_query()

        if sql_query:
            self.env.cr.execute(sql_query)
            prices = self.env.cr.fetchall()

            Console.debug('[Prestadoo] Se van a volcar {} registros'.format(len(prices)))
            if prices:
                Jesie.insert_jesie_prices(prices, self.version, self.row_insert_limit)
            Console.debug('[Prestadoo] {} registros volcados'.format(len(prices)))

            Console.debug('[Prestadoo] FIN de proceso de volcado de precios específicos de clientes')
        else:
            Console.debug('[Prestadoo] No existe la consulta')

    def launch_jesie_enqueue(self):
        Console.debug('[Prestadoo] Llamada a procedimiento almacenado OdooEnqueuePrices')

        Jesie.jesie_enqueue_prices()

        Console.debug('[Prestadoo] FIN procedimiento almacenado OdooEnqueuePrices')
        Console.debug('[Prestadoo] Version de precios: {}'.format(self.version))
