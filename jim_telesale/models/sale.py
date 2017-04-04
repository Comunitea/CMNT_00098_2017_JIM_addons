# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def confirm_order_background(self, order_id):
        """
        OWERWRITED in order to pass the state to pending or lqdr
        """
        self.browse(order_id).action_lqdr_pending()

    @api.model
    def _get_ts_line_vals(self, order_obj, line):
        """
        Get the firtst product route to the line
        """
        t_product = self.env['product.product']
        product_obj = t_product.browse(line['product_id'])
        vals = super(SaleOrder, self)._get_ts_line_vals(order_obj, line)

        if product_obj.route_ids:
            vals.update({'route_id': product_obj.route_ids[0].id})
        return vals
