# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils

import logging
_logger = logging.getLogger(__name__)


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

    def _get_ic_sale(self, sales):
        sale = sales.filtered(lambda x: x.auto_generated == True)
        ic_purchase = self.env['purchase.order'].sudo(). \
            browse(sale.mapped('auto_purchase_order_id').id)
        sales = self.env['sale.order'].search(
            [('procurement_group_id', 'in', [ic_purchase.mapped(
                'group_id').id])])
        sale = sales.filtered(lambda x: x.auto_generated == False)
        return sale and sale[0] or False

    @api.multi
    def _compute_orig_sale(self):
        for record in self:
            name = ''
            id = False
            sale = []
            if record.group_id:
                sales = self.env['sale.order'].search(
                    [('procurement_group_id', '=', record.group_id.id)])
                sale = sales.filtered(lambda x : x.auto_generated == False)
                if sale:
                    sale = sale[0]
                elif sales:
                    sale = self.sudo()._get_ic_sale(sales)
            if sale:
                record.orig_sale_str = sale.name
                record.orig_sale_id = sale



    orig_sale_id = fields.Many2one('sale.order', 'Origen', compute=_compute_orig_sale, multi=True)
    orig_sale_str = fields.Char('Sale order', compute=_compute_orig_sale, multi=True)
    ready = fields.Boolean('Revision Ready', default=False, readonly=True)
    unreserve_done = fields.Boolean('Unreserve done', default=False, copy=False)

    @api.model
    def _prepare_values_extra_move(self, op, product, remaining_qty):
        vals = super(StockPicking, self)._prepare_values_extra_move(op, product, remaining_qty)
        vals['company_id'] = op.picking_id.company_id.id
        vals['extra_move'] = True
        return vals

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
        for picking in self:
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
        self.write({'unreserve_done': False})
        res = super(StockPicking, self).action_cancel()


    def get_next_pick(self):
        next_pick = False
        pick_id = self and self[0]
        move = pick_id.move_lines and pick_id.move_lines[0]
        if move:
            if move.move_dest_id.picking_id.sale_id \
                    and not move.picking_id.purchase_id.intercompany \
                    and not move.move_dest_id.picking_id.sale_id.auto_generated:
                next_pick = move.move_dest_id.picking_id
            elif move.move_dest_IC_id.id \
                    and not move.move_dest_IC_id.picking_id.sale_id.auto_generated:
                next_pick = move.move_dest_IC_id.picking_id
        return next_pick

    def propagate_pick_values(self):
        ##Propagamos peso y numero de bultos y lo que me haga falta
        try:
            pick_id = self and self[0]
            if not pick_id:
                return
            next_pick = pick_id.get_next_pick()
            _logger.info("Propago valores de %s " % pick_id.name)
            if next_pick:
                _logger.info("Propago valores de %s al albaran %s" % (pick_id.name, next_pick.name))
                pick_packages = next_pick.pick_packages + pick_id.pick_packages
                pick_weight = next_pick.pick_weight + pick_id.pick_weight
                next_pick_vals = {'pick_packages': pick_packages,
                                  'pick_weight': pick_weight}
                _logger.info("Paquetes y volumen {}".format(next_pick_vals))
                if pick_id.carrier_id and not next_pick.carrier_id:
                    _logger.info("Transportista:{}".format(pick_id.carrier_id.id))
                    carrier_id = pick_id.carrier_id.id
                    next_pick_vals['carrier_id'] = carrier_id
                if pick_id.operator and not next_pick.operator:
                    operator = next_pick.operator or pick_id.operator
                    _logger.info("Operador")
                    next_pick_vals['operator'] = operator
                next_pick.write(next_pick_vals)
            else:
                _logger.info("No se ha encontrado pick al que propagar los datos")
            _logger.info("Propagarcion de valores: OK")
        except:
            _logger.info("HA OCURRIDO UN ERROR NO PREVISTO")
            pass
        return

    @api.multi
    def do_transfer(self):
        user_id = self.env.user
        ctx = self._context.copy()
        ctx.update(user_name= user_id.name)
        self = self.with_context(ctx)
        self.ensure_one()
        # Si es de una compra intercompañía llamamos al do_transfer de la venta relacionada anterior
        if self.purchase_id.intercompany:
            ic_sale = self.env['sale.order'].sudo().search([('auto_purchase_order_id', '=', self.purchase_id.id)])
            for picking in ic_sale.picking_ids.filtered(lambda x:
                    x.location_dest_id.usage == 'customer' and
                    x.sale_id.auto_generated and
                    x.state not in ['done', 'cancel']):
                #self.intercompany_picking_process(picking)
                picking.action_assign()
                self.propagate_op_qty(picking)

                picking.do_transfer()
        #Si es entrega a cliente buscar lineas en albaranes de compra intercompañia
        if self.picking_type_id.code == 'outgoing':
            ic_purchases = self.env['purchase.order'].search([('group_id', '=', self.group_id.id),
                                                              ('intercompany', '=', True)])
            if ic_purchases:
                picking_in_ids = ic_purchases.mapped('picking_ids').filtered(
                    lambda x: x.picking_type_id.code == 'internal'
                    and x.location_id.usage == 'supplier' and x.state not in ['done', 'cancel'])
                for ic_purchase_picking in picking_in_ids:
                    #self.intercompany_picking_process(ic_purchase_picking)
                    self.propagate_op_qty(ic_purchase_picking)
                    ops_to_do = \
                        ic_purchase_picking.pack_operation_product_ids\
                            .filtered(lambda x: x.qty_done > 0)
                    if ops_to_do:
                        ic_purchase_picking.do_transfer()

        message = "El usuario <em>{}</em> ha validado el albarán {}<ul><li>Último estado: {}</li><li>Hora de validacion: {}</li>".format(self._context.get('user_name', user_id.name), self.name, self.state, fields.Datetime.now())
        res = super(StockPicking, self).do_transfer()
        self.message_post(message)
        # Propaga la aignacion movimientos realizado a la compra IC y albaŕn
        #  de salida si debe hacerlo

        self.move_lines.propagate_assign_IC()

        return res

    def propagate_op_qty (self, picking):
        for op in self.pack_operation_product_ids:
            pick_op = picking.pack_operation_product_ids.filtered(lambda x:
                    x.product_id.id == op.product_id.id)
            if pick_op and pick_op.qty_done != op.qty_done:
                pick_op.qty_done = op.qty_done
                pick_op.product_qty = op.qty_done



    def _create_extra_moves(self):
        '''This function creates move lines on a picking, at the time of do_transfer, based on
        unexpected product transfers (or exceeding quantities) found in the pack operations.
        '''
        # TDE FIXME: move to batch
        moves = super(StockPicking, self)._create_extra_moves()
        new_moves = self.env['stock.move']
        if moves:
            for move in moves:
                if not move.picking_id.purchase_id.intercompany:
                    # si fuese compra IC no intentan propagar
                    new_moves |= move.propagate_new_moves()
            if new_moves:
                # No computan los movimientos extra para las  cantidades
                # ordenadas
                new_moves.write({'ordered_qty': 0})
                new_moves.with_context(skip_check=True).action_confirm()
        return moves

    @api.multi
    def check_received_qty(self):
        pass

    def do_ic_unreserve(self):
        #SOLO SE DEBEN DE DESRESERVAR LA 1ª VEZ DESDE MULTICOMPAÑIA.
        if self.unreserve_done:
            return
        self.unreserve_done = True
        self.do_unreserve()


class StockMove(models.Model):
    _inherit = "stock.move"

    move_dest_IC_id = fields.Many2one('stock.move', 'Destination Move IC',
                                      copy=False, index=True,
                                      help="Optional: next IC stock move when "
                                           "chaining them")
    move_purchase_IC_id = fields.Many2one('stock.move', 'Purchase Move IC',
                                      copy=False, index=True,
                                      help="Optional: Related purchase IC "
                                           "stock move when "
                                           "chaining them")
    extra_move = fields.Boolean('Extra move')

    def _prepare_procurement_from_move(self):
        vals = super(StockMove, self)._prepare_procurement_from_move()
        vals['move_dest_IC_id'] = self.move_dest_IC_id.id or \
                                  self.move_dest_id.move_dest_IC_id.id
        if self.procurement_id.sale_line_id.order_id.partner_id.id == \
                self.product_id.sudo().company_id.partner_id.id:
            vals['no_product_company'] = True

        return vals

    def prepare_propagate_vals(self, product_move, picking):
        self.ensure_one()
        vals = {
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'product_id': self.product_id.id,
            'procurement_id': product_move.procurement_id.id,
            # 'procure_method': 'make_to_order',
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.product_uom_qty,
            'name': self.name,
            'state': 'draft',
            'restrict_partner_id': self.restrict_partner_id,
            'group_id': picking.group_id.id,
            'company_id': picking.company_id.id,
            'extra_move': True,
            'purchase_line_id':product_move.purchase_line_id.id or False,
        }
        return vals

    def propagate_new_moves(self):

        new_moves = self.env['stock.move']
        for move in self:
            product_move = self.search(
                [('picking_id', '=', move.picking_id.id),
                 ('product_id', '=', move.product_id.id),
                 '|', ('move_dest_id', '!=', move.id),
                 ('move_purchase_IC_id', '!=', move.id)])
            if len(product_move) > 1:
                product_move = product_move[0]   ## PARA REVISAR
            if product_move.move_dest_id and \
                    not product_move.picking_id.purchase_id.intercompany:
                picking = product_move.move_dest_id.picking_id
                vals = move.prepare_propagate_vals(product_move.move_dest_id, picking)
                new_move = move.create(vals)
                move.move_dest_id = new_move
                new_moves |= new_move

            if product_move.move_dest_IC_id and \
                    product_move.move_dest_id.picking_id.sale_id.auto_generated:
                picking = product_move.move_dest_IC_id.picking_id
                vals = move.prepare_propagate_vals(
                    product_move.move_dest_IC_id, picking)
                new_move = move.create(vals)
                move.move_dest_IC_id = new_move
                new_moves |= new_move

            if product_move.move_purchase_IC_id:
                picking = product_move.move_purchase_IC_id.picking_id
                vals = move.prepare_propagate_vals(
                    product_move.move_purchase_IC_id, picking)
                new_move = move.create(vals)
                move.move_purchase_IC_id = new_move
                new_moves |= new_move
        if new_moves:
            new_moves |= new_moves.propagate_new_moves()
        return new_moves

    @api.multi
    def action_done(self):
        #Si el movimiento es una compra IC, comprobamos el estado del
        # move_dest_id y si ya está reservado, quietamos el
        # este_move_dest_id porque y alo ha "forzado el picking de la otra
        # compañia
        move_dests = self.env['stock.move']
        for move in self:
            if move.picking_id.purchase_id.intercompany:
                if move.move_dest_id.state in ['assigned']:
                    move_dests |= move
        if move_dests:
            move_dests.write({'propagate': False})

        res = super(StockMove, self).action_done()
        return res

    def propagate_assign_IC(self):
        # solo movimientos hechos
        moves_done = self.sudo().filtered(lambda x: x.state == 'done')

        #miro si el albaran de destino viene de una venta autogenerada > ICOP de Preparación a ICC
        previous_IC_sale = moves_done.mapped('move_dest_id.picking_id.sale_id').auto_generated

        #Busco albarán de salida
        pick_dest_IC = moves_done.mapped('move_dest_IC_id.picking_id')

        #busco el alabrán de salida de la compra intercompañia
        pick_purchase_IC = moves_done.mapped('move_dest_id.move_purchase_IC_id.picking_id')
        if pick_purchase_IC and pick_purchase_IC.state != 'done':
            #HAGO do_ic_unreserve ya que los albaranes de compra ICP solo se deben de  desreservar la primera vez.
            pick_purchase_IC.do_ic_unreserve()

        if pick_dest_IC and previous_IC_sale:

            mov_to_force = self.env['stock.move']
            mov_to_force |= moves_done.filtered(
                lambda move: move.move_dest_id.move_purchase_IC_id and move.move_dest_id.move_purchase_IC_id.state in (
                'waiting', 'confirmed')).mapped('move_dest_id.move_purchase_IC_id')
            mov_to_force |= moves_done.filtered(
                lambda move: move.move_dest_IC_id.state in ('waiting', 'confirmed')).mapped('move_dest_IC_id')
            if mov_to_force:
                mov_to_force.sudo().force_assign()

    def propagate_assign_IC_old(self):

        previous_IC_sale = \
            self.mapped('move_dest_id.picking_id.sale_id.auto_generated')

        #pick_purchase_IC = self.filtered(lambda x: x.state=='done').mapped(
        #    'move_purchase_IC_id.picking_id')
        pick_dest_IC = self.filtered(lambda x: x.state == 'done').mapped(
            'move_dest_IC_id.picking_id')
        if pick_dest_IC and previous_IC_sale:
            # if pick_dest_IC and pick_dest_IC.state != 'done':
            #     pick_dest_IC.do_unreserve()

            pick_purchase_IC = self.filtered(
                    lambda x: x.state == 'done').mapped(
                    'move_dest_id.move_purchase_IC_id.picking_id')
            if pick_purchase_IC and pick_purchase_IC.state != 'done':
                pick_purchase_IC.do_unreserve()

            for move in self.sudo():
                if pick_dest_IC:
                    if move.state == 'done' and move.move_dest_IC_id and \
                            move.move_dest_IC_id.state in (
                            'waiting', 'confirmed'):
                        move.move_dest_IC_id.sudo().force_assign()
                if pick_dest_IC:
                    if move.state == 'done' \
                            and move.move_dest_id.move_purchase_IC_id and \
                            move.move_dest_id.move_purchase_IC_id.state in (
                                    'waiting', 'confirmed'):
                        move.move_dest_id.move_purchase_IC_id.sudo().force_assign()

    @api.multi
    def action_cancel(self):

        for move in self:
            previous_IC_sale = \
                move.move_dest_id.picking_id.sale_id.auto_generated or \
                      False
            if move.sudo().move_dest_IC_id and previous_IC_sale:
                if move.propagate:
                    move.move_dest_IC_id.sudo().action_cancel()
                    # dest_moves = move.move_dest_IC_id.picking_id.move_lines\
                    #     .filtered(
                    #     lambda x: x.product_id.id == \
                    #     move.move_dest_IC_id.product_id.id
                    #               and x.id != move.move_dest_IC_id.id
                    #               and x.state not in ['draft', 'cancel',
                    #                                   'done'])
                    # dest_moves.sudo().do_unreserve()
                    # dest_moves.sudo().force_assign()

                elif move.sudo().move_dest_IC.id.state == 'waiting':
                    # If waiting, the chain will be broken and we are not sure if we can still wait for it (=> could take from stock instead)
                    move.sudo().move_dest_IC_id.write({'state': 'confirmed'})
            if move.sudo().move_purchase_IC_id:
                if move.propagate:
                    move.move_purchase_IC_id.sudo().action_cancel()
                    # dest_moves = move.move_purchase_IC_id.picking_id.move_lines \
                    #     .filtered(
                    #     lambda x: x.product_id.id == \
                    #               move.move_purchase_IC_id.product_id.id
                    #               and x.id != move.move_purchase_IC_id.id
                    #             and x.state not in ['draft', 'cancel', 'done'])
                    # dest_moves.sudo().do_unreserve()
                    # dest_moves.sudo().force_assign()


       # self.write({'move_dest_IC_id': False})
        res = super(StockMove, self).action_cancel()
        return res

    @api.multi
    def split(self, qty, restrict_lot_id=False, restrict_partner_id=False):
        """ Splits qty from move move into a new move"""
        self = self.with_prefetch()
        new_move = super(StockMove, self).split(qty, restrict_lot_id,
                                                restrict_partner_id)
        # El nuevo movimiento no deb tener ordered_qty ya que se conserva en
        #  el original , en el movieminto original, no....
        self.browse(new_move).write({'ordered_qty': 0})
        # Es previo a la venta IC?
        previous_IC_sale = \
           self.move_dest_id.picking_id.sale_id.auto_generated  or False
        #Propagamos el split al movimiento de salida final
        # if new_move and previous_IC_sale and self.sudo().move_dest_IC_id:
        #     new_move_prop_IC = self.sudo().move_dest_IC_id.split(qty)
        #     self.env['stock.move'].browse(new_move).sudo().write({
        #         'move_dest_IC_id': new_move_prop_IC})
        #Propagamos el split al al movimiento de compra intercompañía
        if new_move and self.sudo().move_purchase_IC_id:
            new_move_prop_purchase_IC = self.sudo().move_purchase_IC_id.split(qty)
            self.env['stock.move'].browse(new_move).sudo().write({
                'move_purchase_IC_id': new_move_prop_purchase_IC})
        if new_move and previous_IC_sale and self.sudo().move_dest_IC_id:
            self.env['stock.move'].browse(new_move).sudo().write({
                'move_dest_IC_id': self.env['stock.move'].browse(
                new_move).move_dest_id.move_purchase_IC_id.move_dest_id.id})

        return new_move

    @api.multi
    def force_assign(self):
        return super(StockMove, self).force_assign()