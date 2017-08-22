# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.addons.jesie.jesie import Jesie
from .. import tools
from output_helper import OutputHelper as Console


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

    def get_row_insert_limit(self):
        # Tenemos que hacer inserciones en bloques de 1000 ya que es el máximo permitido. Para esto, utilizaremos
        # un parámetro de Odoo, así se podrá modificar el tamaño en caso de ser necesario.
        param = self.env["ir.config_parameter"]. \
            search([('key', '=', 'prestadoo.pricelist.insert.limit')])

        self.row_insert_limit = 1000

        if not param:
            self.row_insert_limit = 1000
            Console.debug(
                "[Prestadoo] No se ha encontrado parámetro 'prestadoo.pricelist.insert.limit' en 'Configuración "
                "-> Parámetros -> Parámetros del sistema'; se utilizará 1000.")
        else:
            self.row_insert_limit = int(param.value)
            Console.debug("[Prestadoo] Encontrado parámetro 'prestadoo.pricelist.insert.limit'. "
                          "Valor = {}".format(param.value))

    def pricelist_prices_2_jesie(self):
        Console.debug('[Prestadoo] Obteniendo precios de listas de precios')

        sql_query = r"""
                SELECT 
                    'L' as "type",
                    CASE
                        WHEN (pp.legacy_code IS NULL or pp.legacy_code = '') THEN CAST((1000 + pp.id) AS VARCHAR(5))
                        ELSE pp.legacy_code
                    END as "code",
                    COALESCE(pr.default_code, pt.template_code) as "item_code",
                    ppi.fixed_price as "price"
                FROM product_pricelist pp
                    INNER JOIN product_pricelist_item ppi on pp.id = ppi.pricelist_id and ppi.compute_price = 'fixed' 
                                                                                      and ppi.fixed_price is not null
                                                                                      and ppi.sequence = 1
                                                                                      and (date_end is null 
                                                                                            or date_end > now())
                    LEFT JOIN product_product pr on ppi.product_id = pr.id
                                                and	pr.active = True
                                                and (pr.default_code is not null or pr.default_code <> '')
                    INNER JOIN product_template prt on pr.product_tmpl_id = prt.id
                                                and prt.active = True
                                                and prt.sale_ok = True
                                                and prt."type" = 'product'
                                                and prt.company_id = 1
                    LEFT JOIN product_template pt on ppi.product_tmpl_id = pt.id
                                                and	pt.active = True
                                                and pt."type" = 'product'
                                                and pt.company_id = 1
                WHERE pp.company_id is null or pp.company_id = 1
        """

        self.env.cr.execute(sql_query)
        prices = self.env.cr.fetchall()

        Console.debug('[Prestadoo] Se van a volcar {} registros'.format(len(prices)))
        if prices:
            Jesie.insert_jesie_prices(prices, self.version, self.row_insert_limit)
        Console.debug('[Prestadoo] {} registros volcados'.format(len(prices)))

        Console.debug('[Prestadoo] FIN de proceso de volcado de precios de listas de precios')

    def customer_prices_2_jesie(self):
        Console.debug('[Prestadoo] Obteniendo precios específicos de clientes')

        sql_query = """
                SELECT 
                    'C' as "type",
                    c.ref as "code",
                    COALESCE(pr.default_code, pt.template_code) as "item_code",
                    cp.price as "price"
                FROM customer_price cp
                    INNER JOIN res_partner c on cp.partner_id = c.id
                                            and c.active = True
                                            and c.is_company = True
                                            and c.customer = True
                                            and (c.email is not null and c.email <> '')
                                            and (c.web_password is not null and c.web_password <> '')
                                            and c.id = c.commercial_partner_id 
                    LEFT JOIN product_product pr on cp.product_id = pr.id
                                                and	pr.active = True
                                                and (pr.default_code is not null or pr.default_code <> '')
                    INNER JOIN product_template prt on pr.product_tmpl_id = prt.id
                                                and prt.active = True
                                                and prt.sale_ok = True
                                                and prt."type" = 'product'
                                                and prt.company_id = 1
                    LEFT JOIN product_template pt on cp.product_tmpl_id = pt.id
                                                and	pt.active = True
                                                and pt."type" = 'product'
                                                and pt.company_id = 1
                WHERE cp.company_id = 1
        """

        self.env.cr.execute(sql_query)
        prices = self.env.cr.fetchall()

        Console.debug('[Prestadoo] Se van a volcar {} registros'.format(len(prices)))
        if prices:
            Jesie.insert_jesie_prices(prices, self.version, self.row_insert_limit)
        Console.debug('[Prestadoo] {} registros volcados'.format(len(prices)))

        Console.debug('[Prestadoo] FIN de proceso de volcado de precios específicos de clientes')

    def launch_jesie_enqueue(self):
        Console.debug('[Prestadoo] Llamada a procedimiento almacenado OdooEnqueuePrices')

        Jesie.jesie_enqueue_prices()

        Console.debug('[Prestadoo] FIN procedimiento almacenado OdooEnqueuePrices')
        Console.debug('[Prestadoo] Version de precios: {}'.format(self.version))
