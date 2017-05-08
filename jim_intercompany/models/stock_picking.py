# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def do_transfer(self):

        pack_operations_ids = self.pack_operation_product_ids.filtered(lambda x: x.qty_done > 0).mapped('id')
        move_lines_ids = self.env['stock.move.operation.link'].search([
            ('operation_id', 'in', pack_operations_ids)]).mapped('move_id').mapped('id')

        ic_purchase_moves = self.env['stock.move'].search([('move_dest_id', 'in', move_lines_ids)]). \
            filtered(lambda x: x.picking_id.purchase_id.intercompany)
        ic_purchase_pickings = ic_purchase_moves.mapped('picking_id')
        ic_purchases = ic_purchase_pickings.mapped('purchase_id')


        #ic_pickings = self.search([('group_id', '=', self.group_id.id),('id', '!=', self.id )]).filtered(
        #    lambda x: x.purchase_id.intercompany)

        #ic_purchases = ic_pickings.mapped('purchase_id')
        #ic_purchase_pickings = ic_purchases.mapped('picking_ids')

        ic_purchase_ids = ic_purchases.mapped('id')
        ic_sales = self.env['sale.order'].sudo().search([('auto_purchase_order_id', 'in', ic_purchase_ids)])
        ic_sale_pickings = ic_sales.mapped('picking_ids').filtered(
            lambda x: x.sale_id.auto_generated)

        #Recorre y procesa los albaranes de la venta intercompañía
        for ic_sale_picking in ic_sale_pickings:
            self.intercompany_picking_process(ic_sale_picking)

        # Recorre y procesa los albaranes de la compra intercompañía
        for ic_purchase_picking in ic_purchase_pickings:
            self.intercompany_picking_process(ic_purchase_picking)

        res = super(StockPicking, self).do_transfer()
        return res

    @api.multi
    def intercompany_picking_process(self, picking):
        if picking.state != 'assigned':
            if picking.state in ['waiting', 'confirmed', 'partially_available']:
                message = _("This picking has been forced by intercompany operation %s") % (self.name)
                picking.message_post(body=message)
                picking.force_assign()

        for pack_operation in picking.pack_operation_product_ids:
            origin_pack_operation = self.pack_operation_product_ids.filtered(
                lambda x: x.product_id.id == pack_operation.product_id.id)
            if origin_pack_operation:
                pack_operation.qty_done = origin_pack_operation.qty_done
        if picking.state == 'assigned':
            picking.do_transfer()

    @api.multi
    def check_received_qty(self):
        pass


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def action_done(self):
        for move in self:
            if move.move_dest_id.picking_id.sale_id.auto_generated:
                move.process_intercompany_chain()
        return super(StockMove, self).action_done()

    @api.multi
    def process_intercompany_chain(self):
        ic_purchase = self.sudo().move_dest_id.picking_id.sale_id.auto_purchase_order_id
        if ic_purchase:
            ic_purchase_move = ic_purchase.picking_ids.move_lines.filtered(
                lambda x: x.product_id.id == self.product_id.id)
            ic_purchase_move.move_dest_id.force_assign()
            message = _("The move for product %s  has been forced by intercompany operation %s from company %s") % (
                self.product_id.name, self.picking_id.name, self.picking_id.company_id.name)
            ic_purchase_move.move_dest_id.picking_id.message_post(body=message)


