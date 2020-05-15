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

    @api.multi
    def get_export_product_qtys_prices(self, products_qtys):
        """
        Return list touple of product_id, qty, price, item_id for this pricelists:
        """
        res = []

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # qtys = map(lanmbda x: (x, 1, 1), products)
        # res = dict((product_id, res_tuple[0]) for product_id, res_tuple in self._compute_price_rule(qtys).iteritems())
        
        tot = len(products_qtys)
        idx = 0
        a = datetime.now()
        _logger.info('Iniciamos tarifa {} en {}'.format(self.name, datetime.now()))
        product_ids = [x[0] for x in products_qtys]
        products = self.env['product.product'].browse(product_ids)
        qtys = [x[1] for x in products_qtys]
        item_ids = [x[2] for x in products_qtys]
        recod_prod_qtys = zip(products, qtys, item_ids)
        for t in recod_prod_qtys:
            product = t[0]
            idx += 1
            _logger.info("{} / {}".format(idx, tot))
            price = self.get_product_price(product, t[1], False, False)
            res.append((product.id, t[1], price, t[2]))
        b = datetime.now()
        _logger.info('Finalizamos tarifa {} en {}'.format(self.name, datetime.now()))
        _logger.info('TOTAL: {}'.format(b - a))

        # MUY LENTO CON Y SIN PREFETCH, MEJOR TENERLO
        # read_info = products.with_context(prefetch_fields=False, pricelist=12).read(['price'])
        return res


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'

    @api.multi
    def write(self, vals):
        """
        Si cambia el producto A a B, debría recalcular el precio en todas las
        tarifas implicadas el prodcto A (B se recalculará por el write)
        (el producto que cambio podría estar en otro item de la misma tarifa,
         con precio) con lo que vuelvo a recalcular.
        Esto de recalcular lo hará el cron, yo creo una copia del item en la
        tabla auxiliar 
        """
        if 'product_id' in vals or 'product_tmpl_id' in vals or \
                'categ_id' in vals or 'applied_on' in vals or \
                'base_pricelist_id' in vals:
            self.create_in_aux_table()
        return super(ProductPricelistItem, self).write(vals)

    @api.multi
    def unlink(self):
        """
        Creo una copia del item en la tabla auxiliar para calcular despues los
        productos afectados
        """
        self.create_in_aux_table()
        return super(ProductPricelistItem, self).unlink()
    
    @api.multi
    def create_in_aux_table(self):
        """
        Creo una copia en la tabla auxiliar, lista para ser leida por el mismo
        sql que lee los items a actualizar. De este modo entrará en el flujo ya
        programado para el cálculo de precios en las tarifas implicadas
        """
        for item in self:
            item_info = {
                'item_id': item.id,
                'applied_on': item.applied_on,
                'product_id':item.product_id.id,
                'product_tmpl_id': item.product_tmpl_id.id,
                'categ_id': item.categ_id.id,
                'min_quantity': item.min_quantity,
                'compute_price': item.compute_price,
                'base': item.base,
                'base_pricelist_id': item.base_pricelist_id.id,
                'pricelist_id': item.pricelist_id.id,
            }
            self.env['aux.export'].create(item_info)

    def button_edit_items(self):
        self.ensure_one()
        view = self.env.ref(
            'product.product_pricelist_item_form_view'
        )
        ctx = self.env.context.copy()
        ctx.update(default_pricelist_id=self.pricelist_id.id)
        return {
            'name': _('Agents'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': self.id,
            'context': ctx,
        }