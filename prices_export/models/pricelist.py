# -*- coding: utf-8 -*-
# © 2020 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from datetime import datetime

import logging
_logger = logging.getLogger('--EXPORTACIÓN PRECIOS--')

class ProductPricelist(models.Model):

    _inherit = 'product.pricelist'

    to_export = fields.Boolean('To export')

    # METODO A
    # @api.multi
    # def _exist_global_product_price_rule(self):
    #     """
    #     OPTIMIZACIÓN SQL: ya que con filtered se demora bastante esta consulat
    #     Devuelvo todos los produc
    #     """
    #     res = False
    #     self.ensure_one()
    #     sql = """
    #     select id from product_pricelist_item 
    #     where pricelist_id = {} and 
    #         applied_on = '3_global' and base = 'list_price'
    #     """.format(self.id) 
    #     self._cr.execute(sql)
    #     sql_res = self._cr.fetchall()
    #     if sql_res:
    #         res = True
    #     return False # TODO quitar, solo desarrollo
    
    # METODO A
    # @api.multi
    # def get_related_products(self):
    #     """
    #     Devuelvo los productos asociados a esta tarifa
    #     """
    #     # import ipdb; ipdb.set_trace()
    #     self.ensure_one()
    #     # import ipdb; ipdb.set_trace()
    #     res = self.env['product.product']
    #     # if self.item_ids.with_context(prefetch_fields=False).filtered(lambda x: x.applied_on == '3_global' and x.base == 'list_price'):
    #     # if self.item_ids.filtered(lambda x: x.applied_on == '3_global' and x.base == 'list_price'):
    #     if self._exist_global_product_price_rule():
    #         # (No debería darse en jim) Si hay global basado en precio al 
    #         # publico necesito todos los productos activos
    #         return res.search([])
    #     domain = [
    #         ('pricelist_id', '=', self.id),
    #         ('applied_on', '=', '0_product_variant'),
    #         ('product_id.active', '=', True),
    #     ]
    #     item_ids = self.env['product.pricelist.item'].with_context(prefetch_fields=False).search(domain)
    #     products =  item_ids.mapped('product_id')
    #     # products =  self.item_ids.filtered(lambda x: x.applied_on == '0_product_variant' and x.product_id.active).mapped('product_id')
    #     res |= products
    #     domain = [
    #         ('pricelist_id', '=', self.id),
    #         ('applied_on', '!=', '0_product_variant'),
    #         '|',
    #         ('product_tmpl_id.active', '=', True),
    #         ('categ_id.active', '=', True)
    #     ]
    #     item_ids = self.env['product.pricelist.item'].with_context(prefetch_fields=False).search(domain)
    #     i = 0
    #     tot = len(item_ids)
    #     for item in item_ids:
    #         i += 1
    #         _logger.info('proceso {}/{}'.format(i, tot))
    #         res |= item.get_item_related_products()
    #     # import ipdb; ipdb.set_trace()
    #     return  res
    #     # return res.search([])
    

    # # METODO A
    # @api.multi
    # def get_export_product_prices(self, products):
    #     """
    #     Return list touple of product_id, price for this pricelists:
    #     """
    #     res = []

    #     # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
    #     # qtys = map(lanmbda x: (x, 1, 1), products)
    #     # res = dict((product_id, res_tuple[0]) for product_id, res_tuple in self._compute_price_rule(qtys).iteritems())
        
    #     # import ipdb; ipdb.set_trace()
    #     tot = len(products)
    #     idx = 0
    #     a = datetime.now()
    #     _logger.info('Iniciamos tarifa {} en {}'.format(self.name, datetime.now()))
    #     for product in products:
    #         idx += 1
    #         _logger.info("{} / {}").format(idx, tot)
    #         price = self.get_product_price(product, 1, 1, False)
    #         res.append((product.id, price))
    #     b = datetime.now()
    #     _logger.info('Finalizamos tarifa {} en {}'.format(self.name, datetime.now()))
    #     _logger.info('TOTAL: {}'.format(b - a))

    #     # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
    #     # read_info = products.with_context(prefetch_fields=False, pricelist=12).read(['price'])
    #     # import ipdb; ipdb.set_trace()
    #     return res

    # METODO B
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
        _logger.info('Iniciamos tarifa {} en {}'.format(self.name, datetime.now()))
        # import ipdb; ipdb.set_trace()
        # product_ids = list(set([x[0] for x in products_qtys]))
        product_ids = [x[0] for x in products_qtys]  # Esto me da alguno repetido
        products = self.env['product.product'].browse(product_ids)
        qtys = [x[1] for x in products_qtys]
        recod_prod_qtys = zip(products, qtys)
        # import ipdb; ipdb.set_trace()
        for t in recod_prod_qtys:
            # product = self.env['product.product'].browse(t[0])
            product = t[0]
            idx += 1
            _logger.info("{} / {}".format(idx, tot))
            price = self.get_product_price(product, t[1], False, False)
            res.append((product.id, t[1], price))
        b = datetime.now()
        _logger.info('Finalizamos tarifa {} en {}'.format(self.name, datetime.now()))
        _logger.info('TOTAL: {}'.format(b - a))

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # read_info = products.with_context(prefetch_fields=False, pricelist=12).read(['price'])
        # import ipdb; ipdb.set_trace()
        return res


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'
    
    # METODO A
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
    #         # SLOW no debería entrar aqui si ya filtrñe antes
    #         res = self.product_id
    #     elif self.applied_on == '1_product':
    #         domain = [('product_tmpl_id', '=', self.product_tmpl_id.id)]
    #         res = self.env['product.product'].search(domain)
    #         # res = self.product_tmpl_id.product_variant_ids
    #     elif self.applied_on == '2_product_category':
    #         domain = [('product_tmpl_id.categ_id', '=', self.categ_id.id)]
    #         res = self.env['prouduct.product'].search(domain)
    #     elif self.applied_on == '3_global':
    #         # Calculo los productos de la tarifa en la que se basa
    #         if self.base == 'pricelist' and self.base_pricelist_id:
    #             # RECURSIVO A LA FUNCIÓN QUE LLAMA A ESTA
    #             res = self.base_pricelist_id.get_related_products()
    #         res = self.env['product.product'].search([])
    #     return res
    
    @api.multi
    def write(self, vals):
        """
        Si cambia el producto A a B, debría recalcular el precio en todas las
        tarifas implicadas el prodcto A (B se recalculará por el write)
        (el producto que cambio podría estar en otro item de la misma tarifa,
         con precio) con lo que vuelvo a recalcular 
        """
        if vals.get('product_id'):
            old_products = self.mapped('product_id')
        res = super(ProductPricelistItem, self).write(vals)
        return self