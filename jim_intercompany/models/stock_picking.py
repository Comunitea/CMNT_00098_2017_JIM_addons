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
        # if picking.state != 'assigned':
        #     if picking.state in ['waiting', 'confirmed', 'partially_available']:
        #         message = _("This picking has been forced by intercompany operation %s") % (self.name)
        #         picking.message_post(body=message)
        #         picking.force_assign()
        #for pack_operation in picking.pack_operation_product_ids:

        origin_pack_operations = self.pack_operation_product_ids.filtered(lambda x: x.qty_done > 0)
        for origin_pack_operation in origin_pack_operations:
            line = picking.move_lines.filtered(lambda x : x.product_id.id == origin_pack_operation.product_id.id)
            #  Si ese producto está en el albárna de compra
            if line:
                if line.state != 'assigned':
                    line.force_assign()
                ops = line.linked_move_operation_ids
                ops[0].qty_done = origin_pack_operation.qty_done

        picking.do_transfer()

    @api.multi
    def view_related_pickings(self):
        pickings = self.browse(self._context.get('active_ids', []))

        #action = self.env.ref('stock.do_view_pickings').read()[0]
        domain = [('group_id', 'in', pickings.mapped('group_id').ids),
                            ('id', 'not in', pickings.mapped('id'))]

        return domain

    @api.multi
    def do_transfer(self):
        self.ensure_one()

        # Si es de una compra intercompañía llamamos al do_transfer de la venta relacionada anterior
        if self.purchase_id.intercompany:
            ic_sale = self.env['sale.order'].sudo().search([('auto_purchase_order_id', '=', self.purchase_id.id)])
            for picking in ic_sale.picking_ids.filtered(lambda x: x.sale_id.auto_generated):
                self.intercompany_picking_process(picking)

        # pack_operations_ids = self.pack_operation_product_ids.filtered(lambda x: x.qty_done > 0).mapped('id')
        # move_lines_ids = self.env['stock.move.operation.link'].search([
        #     ('operation_id', 'in', pack_operations_ids)]).mapped('move_id').mapped('id')

        #Si es entrega a cliente buscar lineas en albaranes de compra intercompañia
        if self.picking_type_id.code == 'outgoing':
            ic_purchases = self.env['purchase.order'].search([('group_id', '=', self.group_id.id),
                                                              ('intercompany', '=', True)])
            if ic_purchases:
                picking_in_ids = ic_purchases.picking_ids.filtered(lambda x: x.picking_type_id.code == 'internal'
                                                                             and x.location_id.usage == 'supplier')
                for ic_purchase_picking in picking_in_ids:
                    self.intercompany_picking_process(ic_purchase_picking)

        # ic_purchase_moves = self.env['stock.move'].search([('move_dest_id', 'in', move_lines_ids)]). \
        #     filtered(lambda x: x.picking_id.purchase_id.intercompany)
        # if ic_purchase_moves:
        #     ic_purchase_pickings = ic_purchase_moves.mapped('picking_id')
        #     ic_purchases = ic_purchase_pickings.mapped('purchase_id')
        #     # Recorre y procesa los albaranes de la compra intercompañía
        #     for ic_purchase_picking in ic_purchase_pickings:
        #         self.intercompany_picking_process(ic_purchase_picking)

        res = super(StockPicking, self).do_transfer()
        return res



    @api.multi
    def check_received_qty(self):
        pass


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        for move in self:
            if move.move_dest_id.picking_id.sale_id.auto_generated:
                move.process_intercompany_chain()
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


