# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class ProcurementRule(models.Model):
    """ Pull rules """
    _inherit = 'procurement.rule'

    procure_method = fields.Selection(
        selection_add=[('company', 'According to the Company')])


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _get_stock_move_values(self):
        vals = super(ProcurementOrder, self)._get_stock_move_values()
        if vals['procure_method'] == 'company':
            if self.env['product.product'].browse(vals['product_id']).company_id.id == vals['company_id']:
                vals['procure_method'] = 'make_to_stock'
            else:
                vals['procure_method'] = 'make_to_order'
        return vals