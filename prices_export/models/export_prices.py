# -*- coding: utf-8 -*-
# © 2020 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from datetime import datetime


class ExportPrices(models.Model):

    _name = 'export.prices'

    product_id = fields.Many2one('product.product', 'Product')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    qty = fields.Float('Min Quantity')
    price = fields.Float('Price')
    
    # @api.model
    # def calculate(self, pricelist_id):
    #     """
    #     Sobre 4 minutos para pvp02, SOLO una vez despues siempre me tarda +25
    #     """
    #     pricelist = self.env['product.pricelist'].browse(pricelist_id)
    #     products = self.env['product.product'].with_context(prefetch_fields=False).search([])
    #     qtys = map(lambda x: (x, 1, 1), products)
    #     print('Iniciamos tarifa {} en {}'.format(pricelist.id, datetime.now()))
    #     a = datetime.now()
    #     # res = pricelist._compute_price_rule(qtys)
    #     pricelist._compute_price_rule(qtys)
    #     b = datetime.now()
    #     print(b - a)
    #     print('Finalizamos tarifa {} en {}'.format(pricelist.id, datetime.now()))
    #     # import ipdb; ipdb.set_trace()
    #     return res

    @api.model
    def create_export_prices_records(self, pricelist, product_prices):
        tot = len(product_prices)
        idx = 0
        for t in product_prices:
            idx += 1
            if not t[1]:
                continue
            print('Creando record producto: {} precio: {} ({}/{})'.format(t[0], t[1], tot, idx))
            vals = {
                'product_id':t[0],
                'pricelist_id': pricelist.id,
                'qty': 1,
                'price':t[1]
            }
            self.create(vals)
    

    @api.model
    def create_export_qtys_prices_records(self, pricelist, product_prices):
        # import ipdb; ipdb.set_trace()
        tot = len(product_prices)
        idx = 0
        for t in product_prices:
            idx += 1
            if not t[1]:
                continue
            print('Creando record producto: {} qty: {}, precio: {} ({}/{})'.format(t[0], t[1], t[2], tot, idx))
            vals = {
                'product_id':t[0],
                'pricelist_id': pricelist.id,
                'qty': t[1],
                'price':t[2]
            }
            self.create(vals)
    
    
    @api.model
    def get_item_related_product_qtys(self, i):
        """
        Devuelvo [(p_id, qty)...] que representan los productos implicados
        por la regla de precios.
        """
        # import ipdb; ipdb.set_trace()
        qty = i['min_quantity']
        res = []
        if i['applied_on'] == '0_product_variant':
            res.append((i['product_id'], qty))
        elif i['applied_on'] == '1_product':
            domain = [('product_tmpl_id', '=', i['product_tmpl_id'])]
            products = self.env['product.product'].search(domain)
            for p in products:
                res.append((p.id, qty))
        elif i['applied_on'] == '2_product_category':
            domain = [('categ_id', '=', self.categ_id.id)]
            res = self.env['product.product'].search(domain)
            for p in products:
                res.append((p.id, qty))
        elif i['applied_on'] == '3_global':
            # import ipdb; ipdb.set_trace()
            # Calculo los productos de la tarifa en la que se basa
            if i['base'] == 'pricelist' and i['base_pricelist_id']:
                # RECURSIVO A LA FUNCIÓN QUE LLAMA A ESTA
                res.extend(
                    self.sql_get_related_products_qtys(i['base_pricelist_id']))
        return res
    

    @api.model
    def sql_get_related_products_qtys(self, pricelist_id):
        """
        Devuelvo los productos asociados a esta tarifa
        """
        # import ipdb; ipdb.set_trace()
        res = []
        item_infos = []
        Pli = self.env['product.pricelist.item']

        # SLOW
        # domain = [('pricelist_id', '=', self.id)]
        # fields = ['applied_on', 'product_id', 'product_tmpl_id', 'categ_id', 'min_quantity', 'compute_price', 'base', 'base_pricelist_id']
        # res = self.env['product.pricelist.item'].search_read(domain, fields)

        sql = """
        select id, applied_on, product_id, product_tmpl_id, categ_id, min_quantity, 
               compute_price, base, base_pricelist_id, pricelist_id 
        from product_pricelist_item where pricelist_id = {};
        """.format(pricelist_id) 
        self._cr.execute(sql)
        sql_res = self._cr.fetchall()
        for t in sql_res:
            item_info = {
                'id': t[0],
                'applied_on': t[1],
                'product_id': t[2],
                'product_tmpl_id': t[3],
                'categ_id': t[4],
                'min_quantity': t[5],
                'compute_price': t[6],
                'base': t[7],
                'base_pricelist_id': t[8],
                'pricelist_id': t[9],
            }
            res2 = self.get_item_related_product_qtys(item_info)
            res.extend(res2)
        return res

    @api.model
    def create_export_prices(self):
        """
        Para todas las tarifas a exportar, calculo sus productos implicados
        obtengo los precios para esos productos, y creo los registros en la
        tabla
        """
        # import ipdb; ipdb.set_trace()
        domain = [
            ('to_export', '=', True),
        ]
        # pricelists = self.env['product.pricelist'].with_context(prefetch_fields=False).search(domain)
        pricelists = self.env['product.pricelist'].search(domain)

        # product_prices = self.calculate(12)
        for pl in pricelists:
            # MANERA LENTA
            a = datetime.now()
            # related_products = pl.get_related_products()
            related_products = self.env['product.product'].search([])
            product_prices = pl.get_export_product_prices(related_products)
            self.create_export_prices_records(pl, product_prices)
           
            # products_qtys = self.sql_get_related_products_qtys(pl.id)
            # product_prices = pl.get_export_product_qtys_prices(products_qtys)
            # self.create_export_qtys_prices_records(pl, product_prices)
            b = datetime.now()
            print('Finalizamos tarifa {} en {}'.format(self.name, datetime.now()))
            print('TOTAL: {}'.format(b - a))
        return


    @api.model
    def compute_export_prices(self, create_all=True):
        """
        Cron que actualiza solo los cambios de precios
        """
        if create_all:
            return self.create_export_prices()

        # import ipdb; ipdb.set_trace()
        # base_date = self.env['ir.config_parameter'].get_param(
        #     'last_call_export_prices', default='')
        # domain = [
        #     ('pricelist_id.to_export', '=', True),
        #     '|',
        #     ('write_date', '>=', base_date),
        #     ('create_date', '>=', base_date),
        # ]
        # items = self.env['product.pricelist.item'].search(domain)

        # for pli in items:
        #     self.create_records(pli)

        # time_now = fields.datetime.now()
        # time_now_str = fields.Datetime.to_string(time_now)
        # self.env['ir.config_parameter'].set_param(
        #     'last_call_export_prices', 'time_now_str')
        return
    
   