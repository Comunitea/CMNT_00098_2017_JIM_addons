# -*- coding: utf-8 -*-
# © 2020 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from datetime import datetime

import logging
_logger = logging.getLogger('--EXPORTACIÓN PRECIOS--')


class ExportPrices(models.Model):

    _name = 'export.prices'

    product_id = fields.Many2one('product.product', 'Product')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    qty = fields.Float('Min Quantity')
    price = fields.Float('Price')
    
    @api.model
    def calculate(self, pricelist_id):
        """
        Sobre 4 minutos para pvp02, SOLO una vez despues siempre me tarda +25
        """
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        products = self.env['product.product'].with_context(prefetch_fields=False).search([])
        qtys = map(lambda x: (x, 1, 1), products)
        _logger.info('Iniciamos tarifa {} en {}'.format(pricelist.id, datetime.now()))
        a = datetime.now()
        # res = pricelist._compute_price_rule(qtys)
        pricelist._compute_price_rule(qtys)
        b = datetime.now()
        _logger.info(b - a)
        _logger.info('Finalizamos tarifa {} en {}'.format(pricelist.id, datetime.now()))
        # import ipdb; ipdb.set_trace()
        return res

    # METODO A
    @api.model
    def create_export_prices_records(self, pricelist, product_prices):
        tot = len(product_prices)
        idx = 0
        for t in product_prices:
            idx += 1
            if not t[1]:
                continue
            _logger.info('Creando record producto: {} precio: {} ({}/{})'.format(t[0], t[1], idx, tot))
            vals = {
                'product_id':t[0],
                'pricelist_id': pricelist.id,
                'qty': 1,
                'price':t[1]
            }
            self.create(vals)
    
    # METODO B
    @api.model
    def create_export_qtys_prices_records(self, pricelist, product_prices):
        # import ipdb; ipdb.set_trace()
        tot = len(product_prices)
        idx = 0
        for t in product_prices:
            idx += 1
            if not t[2]:
                continue
            _logger.info('Creando record producto: {} qty: {}, precio: {} ({}/{})'.format(t[0], t[1], t[2], idx, tot))
            vals = {
                'product_id':t[0],
                'pricelist_id': pricelist.id,
                'qty': t[1],
                'price':t[2]
            }
            self.create(vals)
    
    # METODO B
    @api.model
    def get_item_related_product_qtys(self, i, total_res):
        """
        Devuelvo [(p_id, qty)...] que representan los productos implicados
        por la regla de precios.
        Devuelvo solo los activos
        """
        # import ipdb; ipdb.set_trace()
        qty = i['min_quantity']
        res = []
        if i['applied_on'] == '0_product_variant':
            if (i['product_id'], qty) not in total_res:
                res.append((i['product_id'], qty))
        elif i['applied_on'] == '1_product':
            domain = [('product_tmpl_id', '=', i['product_tmpl_id'])]
            products = self.env['product.product'].search(domain)
            # import ipdb; ipdb.set_trace()
            for p in products:
                if (p.id, qty) not in total_res:
                    res.append((p.id, qty))
        elif i['applied_on'] == '2_product_category':
            domain = [('categ_id', '=', i['product_tmpl_id'])]
            products = self.env['product.product'].search(domain)
            for p in products:
                if (p.id, qty) not in total_res:
                    res.append((p.id, qty))
        elif i['applied_on'] == '3_global':
            # import ipdb; ipdb.set_trace()
            # Calculo los productos de la tarifa en la que se basa
            if i['base'] == 'pricelist' and i['base_pricelist_id']:
                # RECURSIVO A LA FUNCIÓN QUE LLAMA A ESTA
                res.extend(
                    self.sql_get_related_products_qtys(i['base_pricelist_id']))
        return res
    
    # METODO B
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
        select ppi.id, ppi.applied_on, ppi.product_id, ppi.product_tmpl_id, ppi.categ_id, ppi.min_quantity, 
               ppi.compute_price, ppi.base, ppi.base_pricelist_id, ppi.pricelist_id 
        from product_pricelist_item ppi
        left join product_product pp on pp.id=ppi.product_id
        left join product_template pt on pt.id=ppi.product_tmpl_id
        left join product_category pc on pc.id=ppi.categ_id
        where ppi.pricelist_id = {}
        and 
        ( (ppi.applied_on != '3_global') and (pp.active=true or pt.active or pc.active)
         or
        (ppi.applied_on = '3_global'));
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
            res2 = self.get_item_related_product_qtys(item_info, res)
            res.extend(res2)
        return res

    @api.model
    def create_export_prices(self):
        """
        Para todas las tarifas a exportar, calculo sus productos implicados
        obtengo los precios para esos productos, y creo los registros en la
        tabla
        """
        start = datetime.now()
        # import ipdb; ipdb.set_trace()
        domain = [
            ('to_export', '=', True),
        ]
        # pricelists = self.env['product.pricelist'].with_context(prefetch_fields=False).search(domain)
        pricelists = self.env['product.pricelist'].search(domain)

        # product_prices = self.calculate(12)
        for pl in pricelists:
            # import ipdb; ipdb.set_trace()
            a = datetime.now()
            # METODO A MANERA LENTA
            # related_products = pl.get_related_products()
            # related_products = self.env['product.product'].search([])
            # product_prices = pl.get_export_product_prices(related_products)
            # self.create_export_prices_records(pl, product_prices)

            # METODO B al meenos 2 veces mas rápida
            products_qtys = self.sql_get_related_products_qtys(pl.id)
            product_prices = pl.get_export_product_qtys_prices(products_qtys)
            self.create_export_qtys_prices_records(pl, product_prices)

            b = datetime.now()
            _logger.info('Finalizamos tarifa {} en {}'.format(pl.name, datetime.now()))
            _logger.info('TOTAL: {}'.format(b - a))
        end = datetime.now()
        _logger.info('TOTAL EXPORTACION: {}'.format(end - start))
        return

    #************************************************************************** 
    #************************CÁLCULO CAMBIOS DE PRECIOS************************
    #**************************************************************************

    @api.model
    def get_related_pricelist_ids(self, i):
        """
        Para un elemento calculo las tarifas donde deberá recalcularse el
        precio
        """
        # import ipdb; ipdb.set_trace()
        pricelist_id = i['pricelist_id']
        domain = [
            ('pricelist_id.to_export', '=', True),
            ('base_pricelist_id', '=', pricelist_id)
        ]
        items = self.env['product.pricelist.item'].search(domain)
        pricelists = items.mapped('pricelist_id')
        return pricelists._ids
    
    @api.model
    def create_updated_prices(self):
        start = datetime.now()
        # import ipdb; ipdb.set_trace()
        base_date = self.env['ir.config_parameter'].get_param(
            'last_call_export_prices', default='')
        
        # Primera búsqueda rápida por fechas
        domain = [
            ('pricelist_id.to_export', '=', True),
            '|',
            ('write_date', '>=', base_date),
            ('create_date', '>=', base_date),
        ]
        items = self.env['product.pricelist.item'].search(domain)
        # items = self.env['product.pricelist.item'].with_context(prefetch_fields=['applied_on', 'product_id']).search_read(domain,['applied_on', 'product_id'] )
        
        # Búsqueda sql de los activos, ya que el campo applied_on proboca mucha
        # lentitud
        sql = """
        select ppi.id, ppi.applied_on, ppi.product_id, ppi.product_tmpl_id, ppi.categ_id, ppi.min_quantity, 
               ppi.compute_price, ppi.base, ppi.base_pricelist_id, ppi.pricelist_id 
        from product_pricelist_item ppi
        left join product_product pp on pp.id=ppi.product_id
        left join product_template pt on pt.id=ppi.product_tmpl_id
        left join product_category pc on pc.id=ppi.categ_id
        where  ppi.id in {} and
        ( (ppi.applied_on != '3_global') and (pp.active=true or pt.active or pc.active)
         or
        (ppi.applied_on = '3_global'));
        """.format(tuple(items._ids))
        self._cr.execute(sql)
        sql_res = self._cr.fetchall()
        items_info = []
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
            items_info.append(item_info)
        # import ipdb; ipdb.set_trace()

        # Calculo todos los productos qty a actualizar en cada tarifa sin
        # repetirlos
        pricelist2update = {}
        idx = 0
        tot = len(items_info)
        pricelist_computed = []
        for i in items_info:
            idx += 1
            _logger.info('CALCULANDO ITEM: {} /{}'.format(idx, tot))
            pricelist_id = i['pricelist_id']
            
            # Inicializo diccionario tarifas
            if not pricelist_id in pricelist2update:
                pricelist2update[pricelist_id] = []
            
            # Obtengo los productos cantidades asociados a ese item
            products_qtys = self.get_item_related_product_qtys(i, [])

            # Añado los productos,qtys para esta tarifa solo si no están ya.
            for t in products_qtys:
                if t not in pricelist2update[pricelist_id]:
                    pricelist2update[pricelist_id].append(t)
            
            # Busco las tarifas asociadas a recalcular
            # if i['pricelist_id'] not in pricelist_computed:
            related_pricelist_ids = self.get_related_pricelist_ids(i)
            # pricelist_computed.append(i['pricelist_id'])
            _logger.info(' - tarifas relacionadas: {}'.format(related_pricelist_ids))
            for pl_id in related_pricelist_ids:
                if not pl_id in pricelist2update:
                    pricelist2update[pl_id] = []
                # Añado los productos,qtys para esta tarifa solo si no están ya.
                for t in products_qtys:
                    if t not in pricelist2update[pl_id]:
                        pricelist2update[pl_id].append(t)

        # Para cada tarifa tenfo sus [(productos, qtys)...] los paso a la
        # función de la tarifa que me devuelve los precios en formato
        # [(prod,qty,price)...], despues creo todos los registros para
        # esa tarifa
        # import ipdb; ipdb.set_trace()
        
        pricelist_ids = pricelist2update.keys()
        pricelists = self.env['product.pricelist'].browse(pricelist_ids)
        idx = 0
        tot = len(pricelists)
        for pl in pricelists:
            idx += 1
            _logger.info('CREANDO REGISTROS TARIFA {} {}/{} '.format(pl.name, idx, tot))
            products_qtys = pricelist2update[pl.id]
            product_prices = pl.get_export_product_qtys_prices(products_qtys)
            self.create_export_qtys_prices_records(pl, product_prices)
        end = datetime.now()
        _logger.info('TOTAL EXPORTACION: {}'.format(end - start))

    #************************************************************************** 
    #******************************** CRON ************************************ 
    #**************************************************************************

    @api.model
    def compute_export_prices(self, create_all=True):
        """
        Cron que actualiza solo los cambios de precios
        """
        create_all = True
        if create_all:
            return self.create_export_prices()
        else:
            return self.create_updated_prices()
        # import ipdb; ipdb.set_trace()
       

        # time_now = fields.datetime.now()
        # time_now_str = fields.Datetime.to_string(time_now)
        # self.env['ir.config_parameter'].set_param(
        #     'last_call_export_prices', 'time_now_str')
        return
    
   