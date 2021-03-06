# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    color_id = fields.Many2one('product.attribute.value', 'Color',
                               readonly=True)
    size_id = fields.Many2one('product.attribute.value', 'Size',
                               readonly=True)

    def _select(self):

        res = super(SaleReport, self)._select()
        res = res + """, 
                    (SELECT pav.id FROM product_attribute_value pav INNER JOIN product_attribute_value_product_product_rel pavppr
				on pavppr.product_attribute_value_id = pav.id
				INNER JOIN  product_attribute pa on pav.attribute_id = pa.id 
				WHERE pavppr.product_product_id = product_id and pa.is_color = True LIMIT 1)
		 as color_id,
			(SELECT pav.id FROM product_attribute_value pav INNER JOIN product_attribute_value_product_product_rel pavppr
				on pavppr.product_attribute_value_id = pav.id
				INNER JOIN  product_attribute pa on pav.attribute_id = pa.id 
				WHERE pavppr.product_product_id = product_id and pa.is_color = False LIMIT 1)
		 as size_id
                    """
        return res

    def _group_by(self):
        return super(SaleReport, self)._group_by() + ", color_id, size_id"

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
                %s
                FROM ( %s )
                %s
                )""" % (
        self._table, self._select(), self._from(), self._group_by()))
