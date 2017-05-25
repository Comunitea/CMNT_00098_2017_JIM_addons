# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, api
import time


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def confirm_order_background(self, order_id):
        """
        OWERWRITED in order to pass the state to pending or lqdr
        """
        self.browse(order_id).action_lqdr_option()

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
        vals.update({'chained_discount': line.get('chained_discount', '0.00'),
                     'name': line.get('description', '')})
        return vals

    @api.model
    def _get_ts_template_line_vals(self, order_obj, line):
        vals = super(SaleOrder, self).\
            _get_ts_template_line_vals(order_obj, line)
        t_product = self.env['product.product']
        product_obj = t_product.browse(line['product_id'])
        if product_obj.route_ids:
            vals.update({'route_id': product_obj.route_ids[0].id})
        vals.update({'name': line.get('description', ''),
                     'chained_discount': line.get('chained_discount', '0.00')})
        return vals

    @api.model
    def _get_ts_parent_template_line_vals(self, order_obj, line, total_qty):
        vals = super(SaleOrder, self).\
            _get_ts_parent_template_line_vals(order_obj, line, total_qty)
        t_product = self.env['product.product']
        product_obj = t_product.browse(line['product_id'])
        if product_obj.route_ids:
            vals.update({'route_id': product_obj.route_ids[0].id})
        vals.update({'name': line.get('description', ''),
                     'chained_discount': line.get('chained_discount', '0.00')})
        return vals

    @api.model
    def ts_onchange_partner_id(self, partner_id):
        """
        Get warning messagges
        """
        res = super(SaleOrder, self).ts_onchange_partner_id(partner_id)
        order_t = self.env['sale.order']
        partner = self.env['res.partner'].browse(partner_id)

        order = order_t.new({'partner_id': partner_id,
                             'date_order': time.strftime("%Y-%m-%d"),
                             'pricelist_id':
                             partner.property_product_pricelist.id})
        res2 = order.onchange_partner_id_warning()
        warning = False

        if res2 and res2.get('warning', False):
            warning = res2['warning']['message']

        mode = 'warning'
        if partner.sale_warn == 'block':
            mode = 'block'
        res.update({
            'warning': warning,
            'mode': mode

        })
        return res

    @api.model
    def ts_action_proforma(self, order_id):
        self.browse(order_id).action_proforma()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def ts_product_id_change(self, product_id, partner_id, pricelist_id):
        """
        Get available stock in each call to product_id_change from
        telesale interface.
        """
        res = super(SaleOrderLine, self).ts_product_id_change(product_id,
                                                              partner_id,
                                                              pricelist_id)
        if product_id:
            product = self.env['product.product'].browse(product_id)
            res.update({'global_available_stock':
                        product.global_available_stock})
        return res
