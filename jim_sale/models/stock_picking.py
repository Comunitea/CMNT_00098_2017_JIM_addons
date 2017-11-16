# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"


    def show_packs_in_pick(self):
        ids = []
        for op in self.pack_operation_ids:
            ids.append(op.id)
        view_id = self.env['ir.model.data'].xmlid_to_res_id(
            'jim_sale.stock_pack_picks_tree')
        #view_id = self.env.ref('stock_pack_picks_tree').id
        return {
            'domain': "[('id','in', " + str(ids) + ")]",
            'name': _('Packing List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'view_id': view_id,
            'context': False,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def do_transfer(self):
        return super(StockPicking, self).do_transfer()

    def _add_delivery_cost_to_so(self):
        #Eliminamos la funcioanalidad de ñadir el producto al pedido
        pass
        # self.ensure_one()
        # sale_order = self.sale_id
        # if sale_order.invoice_shipping_on_delivery:
        #     sale_order._create_delivery_line(self.carrier_id, self.carrier_price)

    def ordered_qty_to_qty_done(self):
        for op in self.pack_operation_product_ids:
            if op.qty_done == 0:
                op.qty_done = op.ordered_qty

    # @api.one
    # @api.depends('move_lines.procurement_id.sale_line_id.order_id')
    # def _compute_sale_id(self):
    #
    #     super(StockPicking, self)._compute_sale_id()
    #
    #     for move in self.move_lines:
    #         move_sale = move.move_dest_IC_id or move.move_dest_id or move
    #         sale_line = move_sale.procurement_id.sale_line_id
    #         if sale_line:
    #             self.sale_id = sale_line.order_id
    #         return

