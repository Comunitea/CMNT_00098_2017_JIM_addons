# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, api, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    route_name = fields.Char('Route name', related='route_ids.name',
                             store=True)

    @api.model
    def ts_get_global_stocks(self, product_id):
        """ Return data of widget productInfo """
        res = {'global_available_stock': 0.0}
        if product_id:
            product_obj = self.browse(product_id)
            res.update({'global_available_stock':
                        product_obj.global_available_stock})
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # When open grid return global_available_stock
    @api.model
    def _get_variant_stock(self, product):
        super(ProductTemplate, self)._get_variant_stock(product)
        return product and product.global_available_stock or 0
