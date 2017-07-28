# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    count_picking_review = fields.Integer(compute='_compute_picking_review_count')

    @api.multi
    def _compute_picking_review_count(self):
        # TDE TODO count picking can be done using previous two
        domain = [('state', 'in', ('assigned', 'waiting', 'partially_available')),
                                      ('ready', '=', True)]

        data = self.env['stock.picking'].read_group(domain +
                                                        [('state', 'not in', ('done', 'cancel')),
                                                         ('picking_type_id', 'in', self.ids)],
                                                        ['picking_type_id'], ['picking_type_id'])
        count = dict(
            map(lambda x: (x['picking_type_id'] and x['picking_type_id'][0], x['picking_type_id_count']), data))
        for record in self:
            record['count_picking_review'] = count.get(record.id, 0)

    @api.multi
    def get_action_picking_tree_review(self):
        return self._get_action('jim_intercompany.action_picking_tree_review')

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def toggle_ready(self):
        """ Inverse the value of the field ``ready`` on the records in ``self``. """
        for record in self:
            record.ready = not record.ready

    ready = fields.Boolean('Revision Ready', default=False, readonly=True)

    @api.model
    def _prepare_values_extra_move(self, op, product, remaining_qty):
        vals = super(StockPicking, self)._prepare_values_extra_move(op, product, remaining_qty)
        vals['company_id'] = op.picking_id.company_id.id
        return vals

    @api.multi
    def intercompany_picking_process(self, picking):
        picking = picking.with_context(force_company=picking.company_id.id, company_id=picking.company_id.id)

        origin_pack_operations = self.pack_operation_product_ids.filtered(lambda x: x.qty_done > 0)
        origin_products = origin_pack_operations.mapped('product_id')
        for origin_product in origin_products:
            orig_product_qty = sum(x.product_qty
                                   for x in origin_pack_operations.filtered(lambda x:
                                                                            x.product_id.id == origin_product.id))
            lines = picking.move_lines.filtered(lambda x : x.product_id.id == origin_product.id)
            assigned_lines = lines.filtered(lambda x: x.state == 'assigned')
            assigned_qty = sum(x.product_qty for x in assigned_lines)
            if assigned_qty < orig_product_qty:
                # Buscamos si hay más...
                not_assigned_lines = lines.filtered(lambda x: x.state in ['confirmed', 'waiting'])
                not_assigned_lines.force_assign()
                assigned_lines = lines.filtered(lambda x: x.state == 'assigned')

            ops = assigned_lines.linked_move_operation_ids.mapped('operation_id')
            ops_qty = sum(x.product_qty for x in ops)
            remain_qty = orig_product_qty
            last_op =False
            if len(ops) == 1:
                ops[0].qty_done = ops[0].product_qty = orig_product_qty
                remain_qty = 0
            else:

                for op in ops:
                    if remain_qty == 0:
                        op.unlink()
                    else:
                        if op.product_qty < remain_qty:
                            op.done_qty = op.product_qty
                            remain_qty -= op.product_qty
                        else:
                            op.done_qty = op.product_qty = remain_qty
                            remain_qty = 0
                    last_op = op
            if remain_qty > 0 and last_op:
                last_op.done_qty = last_op.product_qty = last_op.product_qty + remain_qty

        for pack in picking.pack_operation_ids:
            if pack.qty_done <= 0:
                pack.unlink()
        picking.do_transfer()

    @api.multi
    def view_related_pickings(self):
        pickings = self.browse(self._context.get('active_ids', []))
        #action = self.env.ref('stock.do_view_pickings').read()[0]
        groups = pickings.mapped('group_id')
        groups |= pickings.mapped('sale_id.procurement_groups')
        domain = [('group_id', 'in', groups.ids),
                  ('id', 'not in', pickings.mapped('id'))]
        return domain

    @api.multi
    def action_cancel(self):
        for picking in  self:
            if picking.picking_type_id.code == 'outgoing':
                ic_purchases = self.env['purchase.order'].search([('group_id', '=', picking.group_id.id),
                                                                  ('intercompany', '=', True)])
                if ic_purchases:
                    for purchase in ic_purchases:
                        picking_in_ids = \
                            purchase.picking_ids.filtered(lambda x: x.picking_type_id.code == 'internal'
                                                         and x.location_id.usage == 'supplier'
                                                         and x.state != 'done')
                    #CANCELA ALBARANES DE COMPRA RELACIONADOS
                        picking_in_ids.action_cancel()

            if picking.purchase_id.intercompany:
                ic_sale = self.env['sale.order'].sudo().search([('auto_purchase_order_id', '=', picking.purchase_id.id)])
                for sale in ic_sale:
                    sale_pickings = sale.picking_ids.filtered(lambda x: x.state != 'done')
                    sale_pickings.action_cancel()

        res = super(StockPicking, self).action_cancel()


    @api.multi
    def do_transfer(self):
        self.ensure_one()

        # Si es de una compra intercompañía llamamos al do_transfer de la venta relacionada anterior
        if self.purchase_id.intercompany:
            ic_sale = self.env['sale.order'].sudo().search([('auto_purchase_order_id', '=', self.purchase_id.id)])
            for picking in ic_sale.picking_ids.filtered(lambda x: x.sale_id.auto_generated):
                self.intercompany_picking_process(picking)

        #Si es entrega a cliente buscar lineas en albaranes de compra intercompañia
        if self.picking_type_id.code == 'outgoing':
            ic_purchases = self.env['purchase.order'].search([('group_id', '=', self.group_id.id),
                                                              ('intercompany', '=', True)])
            if ic_purchases:
                picking_in_ids = ic_purchases.picking_ids.filtered(lambda x: x.picking_type_id.code == 'internal'
                                                                             and x.location_id.usage == 'supplier')
                for ic_purchase_picking in picking_in_ids:
                    self.intercompany_picking_process(ic_purchase_picking)

        res = super(StockPicking, self).do_transfer()
        return res



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
        res = super(StockMove, self).action_done()
        return res

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
            forced_qty = 0
            for x in self.linked_move_operation_ids.mapped('operation_id'):
                forced_qty += x.product_qty
            # forced_qty = sum(x.operation_id.product_qty
            #                  for x in self.linked_move_operation_ids)
            if forced_qty != ic_purchase_move.move_dest_id.product_qty and \
                    ic_purchase_move.move_dest_id.linked_move_operation_ids:
                ic_purchase_move.move_dest_id.linked_move_operation_ids[0].\
                    operation_id.product_qty = forced_qty
                message = _("The quantity for product %s  has been set to %d by intercompany operation %s from company %s") % (
                    self.product_id.name, forced_qty, self.picking_id.name, self.picking_id.company_id.name)
                ic_purchase_move.move_dest_id.picking_id.message_post(body=message)
