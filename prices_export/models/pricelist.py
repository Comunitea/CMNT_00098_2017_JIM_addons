# -*- coding: utf-8 -*-
# © 2020 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from datetime import datetime


class ProductPricelist(models.Model):

    _inherit = 'product.pricelist'

    to_export = fields.Boolean('To export')

    @api.multi
    def _exist_global_product_price_rule(self):
        """
        OPTIMIZACIÓN SQL: ya que con filtered se demora bastante esta consulat
        Devuelvo todos los produc
        """
        res = False
        self.ensure_one()
        sql = """
        select id from product_pricelist_item 
        where pricelist_id = {} and 
            applied_on = '3_global' and base = 'list_price'
        """.format(self.id) 
        self._cr.execute(sql)
        sql_res = self._cr.fetchall()
        if sql_res:
            res = True
        return False # TODO quitar, solo desarrollo
    
    # @api.multi
    # def sql_get_item_ids(self):
    #     res =self.env['product.pricelist.item']
    #     self.ensure_one()
    #     sql = """
    #     select id from product_pricelist_item 
    #     where pricelist_id = {}
    #     """.format(self.id) 
    #     self._cr.execute(sql)
    #     sql_res = self._cr.fetchall()
    #     item_ids = [x[0] for x in sql_res]
    #     import ipdb; ipdb.set_trace()
    #     # res = res.with_context(prefetch_fields=False).browse(self.item_ids._ids)
    #     res = item_ids
    #     return res



    @api.multi
    def get_related_products(self):
        """
        Devuelvo los productos asociados a esta tarifa
        """
        self.ensure_one()
        # import ipdb; ipdb.set_trace()
        res = self.env['product.product']
        # if self.item_ids.with_context(prefetch_fields=False).filtered(lambda x: x.applied_on == '3_global' and x.base == 'list_price'):
        # if self.item_ids.filtered(lambda x: x.applied_on == '3_global' and x.base == 'list_price'):
        # if self._exist_global_product_price_rule():
        #     # (No debería darse en jim) Si hay global basado en precio al 
        #     # publico necesito todos los productos activos
        #     return res.search([])

        # products =  self.item_ids.filtered(lambda x: x.applied_on == '0_product_variant').mapped('product_id')
        # res += products
        # item_ids = self.sql_get_item_ids()
        # item_ids = self.env['product.pricelist.item'].with_context(prefetch_fields=False).search([('pricelist_id', '=', self.id)])
        # for item in item_ids:
        #     res += item.get_item_related_products()
        # import ipdb; ipdb.set_trace()
        # return  res
        return res.search([])
    
    # @api.multi
    # def sql_get_item_ids(self):
    #     res =self.env['product.pricelist.item']
    #     self.ensure_one()
    #     sql = """
    #     select id from product_pricelist_item 
    #     where pricelist_id = {}
    #     """.format(self.id) 
    #     self._cr.execute(sql)
    #     sql_res = self._cr.fetchall()
    #     item_ids = [x[0] for x in sql_res]
    #     import ipdb; ipdb.set_trace()
    #     # res = res.with_context(prefetch_fields=False).browse(self.item_ids._ids)
    #     res = item_ids
    #     return res
        
    @api.multi
    def get_export_product_prices(self, products):
        """
        Return list touple of product_id, price for this pricelists:
        """
        res = []

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # qtys = map(lanmbda x: (x, 1, 1), products)
        # res = dict((product_id, res_tuple[0]) for product_id, res_tuple in self._compute_price_rule(qtys).iteritems())
        
        # import ipdb; ipdb.set_trace()
        tot = len(products)
        idx = 0
        a = datetime.now()
        print('Iniciamos tarifa {} en {}'.format(self.name, datetime.now()))
        for product in products:
            idx += 1
            print("{} / {}").format(idx, tot)
            price = self.get_product_price(product, 1, 1, False)
            res.append((product.id, price))
        b = datetime.now()
        print('Finalizamos tarifa {} en {}'.format(self.name, datetime.now()))
        print('TOTAL: {}'.format(b - a))

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # read_info = products.with_context(prefetch_fields=False, pricelist=12).read(['price'])
        # import ipdb; ipdb.set_trace()
        return res

    # @api.multi
    # def sql_get_related_products_qtys(self):
    #     """
    #     Devuelvo los productos asociados a esta tarifa
    #     """
    #     self.ensure_one()
    #     import ipdb; ipdb.set_trace()
    #     res = []
    #     item_infos = []
    #     Pli = self.env['prodict.pricelist.item']

    #     # SLOW
    #     # domain = [('pricelist_id', '=', self.id)]
    #     # fields = ['applied_on', 'product_id', 'product_tmpl_id', 'categ_id', 'min_quantity', 'compute_price', 'base', 'base_pricelist_id']
    #     # res = self.env['product.pricelist.item'].search_read(domain, fields)

    #     sql = """
    #     select id, applied_on, product_id, product_tmpl_id, categ_id, min_quantity, 
    #            compute_price, base, base_pricelist_id 
    #     from product_pricelist_item where pricelist_id = {};
    #     """.format(self.id) 
    #     self._cr.execute(sql)
    #     sql_res = self._cr.fetchall()
    #     for t in sql_res:
    #         item_info.append({
    #             'id': t[0],
    #             'applied_on': t[1],
    #             'product_id': t[2],
    #             'product_tmpl_id': t[3],
    #             'categ_id': t[4],
    #             'min_quantity': t[5],
    #             'compute_price': t[6],
    #             'base': t[7],
    #             'base_pricelist_id': t[8],
    #         })
    #         res2 = Pli.get_item_related_product_qtys(item_info)
    #     return res


    @api.multi
    def get_export_product_prices(self, products):
        """
        Return list touple of product_id, price for this pricelists:
        """
        res = []

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # qtys = map(lanmbda x: (x, 1, 1), products)
        # res = dict((product_id, res_tuple[0]) for product_id, res_tuple in self._compute_price_rule(qtys).iteritems())
        
        # import ipdb; ipdb.set_trace()
        tot = len(products)
        idx = 0
        a = datetime.now()
        print('Iniciamos tarifa {} en {}'.format(self.name, datetime.now()))
        for product in products:
            idx += 1
            print("{} / {}").format(idx, tot)
            price = self.get_product_price(product, 1, 1, False)
            res.append((product.id, price))
        b = datetime.now()
        print('Finalizamos tarifa {} en {}'.format(self.name, datetime.now()))
        print('TOTAL: {}'.format(b - a))

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # read_info = products.with_context(prefetch_fields=False, pricelist=12).read(['price'])
        # import ipdb; ipdb.set_trace()
        return res

    @api.multi
    def get_export_product_qtys_prices(self, products_qtys):
        """
        Return list touple of product_id, price for this pricelists:
        """
        res = []

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # qtys = map(lanmbda x: (x, 1, 1), products)
        # res = dict((product_id, res_tuple[0]) for product_id, res_tuple in self._compute_price_rule(qtys).iteritems())
        
        # import ipdb; ipdb.set_trace()
        tot = len(products_qtys)
        idx = 0
        a = datetime.now()
        print('Iniciamos tarifa {} en {}'.format(self.name, datetime.now()))
        # import ipdb; ipdb.set_trace()
        product_ids = [x[0] for x in products_qtys]
        products = self.env['product.product'].browse(product_ids)
        qtys = [x[1] for x in products_qtys]
        recod_prod_qtys = zip(products, qtys)
        # import ipdb; ipdb.set_trace()
        for t in recod_prod_qtys:
            # product = self.env['product.product'].browse(t[0])
            product = t[0]
            idx += 1
            print("{} / {}").format(idx, tot)
            price = self.get_product_price(product, t[1], False, False)
            res.append((product.id, t[1], price))
        b = datetime.now()
        print('Finalizamos tarifa {} en {}'.format(self.name, datetime.now()))
        print('TOTAL: {}'.format(b - a))

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # read_info = products.with_context(prefetch_fields=False, pricelist=12).read(['price'])
        # import ipdb; ipdb.set_trace()
        return res


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'
    
    # @api.multi
    # def get_item_related_products(self):
    #     """
    #     Devuelvo los productos implicados por ese elemento
    #     SLOW, los campos .product_id .applied_on...
    #     """
    #     # import ipdb; ipdb.set_trace()
    #     self.ensure_one()
    #     res = self.env['product.product']
    #     if self.applied_on == '0_product_variant':
    #         res = self.product_id
    #     elif self.applied_on == '1_product':
    #         res = self.product_tmpl_id.product_variant_ids
    #     elif self.applied_on == '2_product_category':
    #         domain = [('categ_id', '=', self.categ_id.id)]
    #         res = self.env['prouduct.product'].search(domain)
    #     elif self.applied_on == '3_global':
    #         # Calculo los productos de la tarifa en la que se basa
    #         if self.base == 'pricelist' and self.base_pricelist_id:
    #             # RECURSIVO A LA FUNCIÓN QUE LLAMA A ESTA
    #             res = self.base_pricelist_id.get_related_products()
    #         res = self.env['product.product'].search([])
    #     return res