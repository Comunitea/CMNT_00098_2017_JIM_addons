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
    create_mode = fields.Boolean('Is created')
    # ID DEL ITEM PARA QUE ELLOS BORREN SIEMPRE?
    item_id = fields.Integer('Id item')
    
    
    @api.model
    def create_export_qtys_prices_records(self, pricelist, product_prices, create_mode=False):
        tot = len(product_prices)
        idx = 0

        # Borrar los items que ya existan
        item_ids = [x[3] for x in product_prices]
        item_ids = tuple(item_ids) if item_ids else '(-1)'
        sql = """
        delete
        from export_prices
        where  item_id in {}
        """.format(str(item_ids)).replace(',)', ')')
        self._cr.execute(sql)
        self._cr.commit()

        for t in product_prices:
            idx += 1
            # if not t[2]:  # Si precio 0 ignorar
            #     continue
            _logger.info('Creando record producto: {} qty: {}, precio: {} ({}/{})'.format(t[0], t[1], t[2], idx, tot))
            vals = {
                'product_id':t[0],
                'pricelist_id': pricelist.id,
                'qty': t[1],
                'price':t[2],
                'create_mode': create_mode,
                'item_id': t[3]
            }
            self.create(vals)
    
    @api.model
    def get_item_related_product_qtys(self, i, total_res):
        """
        Devuelvo [(p_id, qty, item_id)...] que representan los productos implicados
        por la regla de precios.
        Devuelvo solo los activos
        """
        # TODO qty, activar cantidades
        # qty = i['min_quantity']
        qty = 1
        res = []
        if i['applied_on'] == '0_product_variant':
            if (i['product_id'], qty, i['id']) not in total_res:
                res.append((i['product_id'], qty, i['id']))
        elif i['applied_on'] == '1_product':
            domain = [('product_tmpl_id', '=', i['product_tmpl_id'])]
            products = self.env['product.product'].search(domain)
            for p in products:
                if (p.id, qty, i['id']) not in total_res:
                    res.append((p.id, qty, i['id']))
        elif i['applied_on'] == '2_product_category':
            domain = [('product_tmpl_id.categ_id', '=', i['categ_id'])]
            products = self.env['product.product'].search(domain)
            for p in products:
                if (p.id, qty, i['id']) not in total_res:
                    res.append((p.id, qty, i['id']))
        elif i['applied_on'] == '3_global':
            # Calculo los productos de la tarifa en la que se basa
            if i['compute_price'] == 'formula' and i['base'] == 'pricelist' and i['base_pricelist_id']:
                # RECURSIVO A LA FUNCIÓN QUE LLAMA A ESTA
                # Debido a que ahora también devuelvo el item_id tengo que
                # corregirlo, porque esto me devuelve el id de la otra tarifa
                rec_res =  self.sql_get_related_products_qtys(i['base_pricelist_id'])
                res2 = [(x[0], x[1], i['id']) for x in rec_res]
                res.extend(res2)
        return res
    
    @api.model
    def sql_get_related_products_qtys(self, pricelist_id):
        """
        Devuelvo los productos asociados a esta tarifa
        """
        res = []

        # Busco por sql sino es lento
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
        domain = [
            ('to_export', '=', True),
        ]
        pricelists = self.env['product.pricelist'].search(domain)
        for pl in pricelists:
            a = datetime.now()
            # Obetener productos-qtys relaccionados
            products_qtys = self.sql_get_related_products_qtys(pl.id)
            # Obtener precios por producto-cantidad
            product_prices = pl.get_export_product_qtys_prices(products_qtys)
            # Crear los registros
            self.create_export_qtys_prices_records(pl, product_prices,
                                                   create_mode=True)

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
    def get_related_items(self, pricelist_id):
        domain = [
            ('pricelist_id.to_export', '=', True),
            ('compute_price', '=', 'formula'),
            ('base_pricelist_id', '=', pricelist_id),
            ('base', '=', 'pricelist'),
        ]
        items = self.env['product.pricelist.item'].search(domain)
        for it in items:
            items |= self.get_related_items(it.pricelist_id.id)
        return items
    
    @api.model
    def create_updated_prices(self):
        # import ipdb; ipdb.set_trace()
        start = datetime.now()
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


        item_ids = tuple(items._ids) if items else '(-1)'
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
        (ppi.applied_on = '3_global'))
        UNION 
        select aux.item_id, aux.applied_on, aux.product_id, aux.product_tmpl_id, aux.categ_id, aux.min_quantity, 
               aux.compute_price, aux.base, aux.base_pricelist_id, aux.pricelist_id
        from aux_export aux
        """.format(str(item_ids)).replace(',)', ')')
        self._cr.execute(sql)
        sql_res = self._cr.fetchall()
        if not sql_res:
            _logger.info('NO SE ENCUENTRAN MODIFICACIONES')
            return
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

        # Calculo todos los productos qty a actualizar en cada tarifa sin
        # repetirlos
        pricelist2update = {}
        idx = 0
        tot = len(items_info)
        # pricelist_computed = []
        for i in items_info:
            idx += 1
            _logger.info('CALCULANDO ITEM: {} /{}'.format(idx, tot))
            pricelist_id = i['pricelist_id']
            
            # Inicializo diccionario tarifas
            if not pricelist_id in pricelist2update:
                pricelist2update[pricelist_id] = []
            
            # Obtengo los productos cantidades asociados a ese item
            # TODO Cantidades, ahora solo devuelvo 1
            products_qtys = self.get_item_related_product_qtys(i, [])

            # Añado los productos,qtys para esta tarifa solo si no están ya.
            for t in products_qtys:
                if t not in pricelist2update[pricelist_id]:
                    pricelist2update[pricelist_id].append(t)

            # Para cada item relaccionado tengo que añadir su ID a la tupla.
            # y recalcular en su tarifa esos productos cantidades
            related_items = self.get_related_items(i['pricelist_id'])
            for rel_it in related_items:
                pl_id = rel_it.pricelist_id.id
                if not pl_id in pricelist2update:
                    pricelist2update[pl_id] = []
                # Añado los productos,qtys para esta tarifa solo si no están ya.
                for t in products_qtys:
                    # TODO REVISAR PARA CANTIDADES, AHORA JUEGO SOLO CON 1
                    # qty = max(t[1], rel_it.min_quantity)
                    qty = 1
                    t2 = (t[0], qty, rel_it.id)
                    t2
                    if t2 not in pricelist2update[pl_id]:
                        # coger el mas grande de los dos???
                        pricelist2update[pl_id].append(t2)
                        # pricelist2update[pl_id].append((t[0], rel_it.min_quantity, rel_it.id))

        # Para cada tarifa tenfo sus [(productos, qtys, item_id)...] los paso a la
        # función de la tarifa que me devuelve los precios en formato
        # [(prod,qty,price)...], despues creo todos los registros para
        # esa tarifa        
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
        return

    #************************************************************************** 
    #******************************** CRON ************************************ 
    #**************************************************************************

    @api.model
    def compute_export_prices(self, create_all=False):
        """
        Cron que actualiza solo los cambios de precios
        """
        if create_all:
            self.create_export_prices()
        else:
            self.create_updated_prices()
        time_now = fields.datetime.now()
        time_now_str = fields.Datetime.to_string(time_now)
        self.env['ir.config_parameter'].set_param(
            'last_call_export_prices', time_now_str)
        
        # Borro la tabla auxiliar
        auxs = self.env['aux.export'].search([])
        auxs.unlink()
        return


class AuxExport(models.Model):

    _name = 'aux.export'

    item_id = fields.Integer('item_id')
    applied_on = fields.Char('applied_on')
    product_id = fields.Integer('product_id')
    product_tmpl_id = fields.Integer('product_tmpl_id')
    categ_id = fields.Integer('categ_id')
    min_quantity = fields.Integer('min_quantity')
    compute_price = fields.Char('compute_price')
    base = fields.Char('Base')
    base_pricelist_id = fields.Integer('base_pricelist_id')
    pricelist_id = fields.Integer('pricelist_id')