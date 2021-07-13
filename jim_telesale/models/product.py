# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, api, fields


class Route(models.Model):
    _inherit = "stock.location.route"

    # Avoid translate in related above because of slow when creae product with
    # translate fields
    name = fields.Char(translate=False)


class ProductProduct(models.Model):
    _inherit = "product.product"

    route_name = fields.Char(
        "Route name", related="route_ids.name", store=True
    )

    # @api.model
    # def ts_get_global_stocks(self, product_id):
    #     """ Return data of widget productInfo """
    #     res = {'global_available_stock': 0.0}
    #     if product_id:
    #         product = self.browse(product_id)
    #         res.update({'global_available_stock':
    #                     product.global_available_stock})
    #     return res

    @api.model
    def get_product_info(self, product_id, partner_id):
        """ Return stock data of widget productInfo """
        res = super(ProductProduct, self).get_product_info(
            product_id, partner_id
        )
        product = self.browse(product_id)
        # route = product.route_ids[0].name if product.route_ids else ""
        # lqdr = _("Yes") if product.lqdr else _("No")
        # res.update({'route': route, 'lqdr': lqdr})
        res.update({"stock": product.global_available_stock})
        return res

    @api.model
    def _get_product_values(self, product):
        """
        Get global available stock from catalog.
        """
        res = super(ProductProduct, self)._get_product_values(product)
        res.update({"stock": product.global_available_stock})
        return res

    @api.model
    def _get_product_stock(self, product):
        """
        Return global available stock when open grid
        """
        super(ProductProduct, self)._get_product_stock(product)
        return product and product.global_available_stock or 0

    @api.model
    def _get_stock_field(self):
        return "global_available_stock"

    @api.model
    def _get_line_discount(self, line):
        res = super(ProductProduct, self)._get_line_discount(line)
        res = line.chained_discount
        return res
