# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _


class StockPicking (models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_open_view_split_ops(self):
        action = self.env.ref(
            'tree_view_ops.action_open_view_split_ops').read()[0]
        action['domain'] = [('id', 'in', self.pack_operation_ids.ids)]
        action['context'] = {
            'default_picking_id': self.id,
        }
        return action


    def ordered_qty_to_qty_done(self):
        for op in self.pack_operation_product_ids.filtered(lambda x:x.qty_done == 0):
            op.qty_done = op.ordered_qty

    def reserved_qty_to_qty_done(self):
        for op in self.pack_operation_product_ids.filtered(lambda x:x.qty_done == 0):
            op.qty_done = op.product_qty

    def reset_qty_done(self):
        for op in self.pack_operation_product_ids.filtered(lambda x:x.qty_done != 0):
            op.qty_done = 0.00


class StockPackOperation (models.Model):
    _inherit = "stock.pack.operation"


    @api.multi
    def reset_op_qty_done(self):
        for op in self.filtered(lambda x: x.qty_done > 0.00 and x.picking_id.state not in ('done', 'draft', 'cancel')):
            op.qty_done = 0.00

    @api.multi
    def op_qty_reserved_to_qty_done(self):
        for op in self.filtered(lambda x: x.qty_done == 0.00 and x.picking_id.state not in ('done', 'draft', 'cancel')):
            op.qty_done = op.product_qty
