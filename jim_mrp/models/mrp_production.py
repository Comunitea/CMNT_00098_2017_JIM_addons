# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


STOCK_TO_REFRESH = 'global_real_stock'

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    global_real_stock = fields.Float('Global Real Stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.")
    web_global_stock = fields.Float('Web stock', readonly=True,
                                    digits=dp.get_precision
                                    ('Product Unit of Measure'))
    @api.multi
    def refresh_stock(self):
        for production in self:
            production.global_real_stock = production.product_id.global_real_stock
            production.web_global_stock = production.product_id.web_global_stock
            for line in production.move_raw_ids:
                line.global_real_stock = line.product_id.global_real_stock
                line.web_global_stock = line.product_id.web_global_stock

    @api.onchange('product_id')
    def refresh_stock_product_id(self):
        if self.product_id:
            self.global_real_stock = self.product_id.global_real_stock
            self.web_global_stock = self.product_id.web_global_stock

    @api.onchange('bom_id')
    def refresh_stock_bom_id(self):
        for line in self.move_raw_ids:
            line.global_real_stock = line.product_id.global_real_stock
            line.web_global_stock = line.product_id.web_global_stock

    @api.model
    def create(self, values):
        if values.get('product_id'):
            product_id = self.env['product.product'].browse(values['product_id'])
            values['global_real_stock'] = product_id.global_real_stock
            values['web_global_stock'] = product_id.web_global_stock
        return super(MrpProduction, self).create(values)

    def _generate_raw_moves(self, exploded_lines):
        moves = super(MrpProduction, self)._generate_raw_moves(exploded_lines)
        if moves:
            for line in moves:
                line.global_real_stock = line.product_id.global_real_stock
                line.web_global_stock = line.product_id.web_global_stock
        return moves




class stock_move(models.Model):
    _inherit = 'stock.move'

    global_real_stock = fields.Float('Global Real Stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.")
    web_global_stock = fields.Float('Web stock', readonly=True,
                                    digits=dp.get_precision
                                    ('Product Unit of Measure'))
