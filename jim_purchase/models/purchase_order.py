# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo.exceptions import AccessError, except_orm
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    @api.depends ('product_id', 'product_qty')
    def _get_line_dimension(self):
        for line in self:
            line.line_volume = 0.00
            line.line_weight = 0.00
            if line.product_id:
                line.line_volume = line.product_id.volume * line.product_qty
                line.line_weight = line.product_id.weight * line.product_qty

    @api.multi
    def get_same_product_purchase_line_ids(self):
        for pol in self:
            pol_ids = self.env['purchase.order.line'].search([('product_id', '=', pol.product_id.id), ('state', '=', 'purchase')])
            pol.purchase_order_line_ids = [(6, 0, pol_ids.ids)]



    line_volume = fields.Float("Volume", compute="_get_line_dimension")
    line_weight = fields.Float("Weight", compute="_get_line_dimension")
    line_info = fields.Char("Line info")
    web_global_stock = fields.Float(related="product_id.web_global_stock")
    purchase_order_line_ids = fields.One2many('purchase.order.line', compute="get_same_product_purchase_line_ids")


    @api.depends('order_id.state', 'move_ids.state')
    def _compute_qty_received(self):

        for line in self:
            if line.order_id.state not in ['purchase', 'done']:
                line.qty_received = 0.0
                continue
            if line.product_id.type not in ['consu', 'product']:
                line.qty_received = line.product_qty
                continue
            total = 0.0
            returns = line.move_ids.filtered(lambda x: x.origin_returned_move_id)
            for move in line.move_ids - returns:
                if move.state == 'done':
                    if move.product_uom != line.product_uom:
                        total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    else:
                        total += move.product_uom_qty

            for move in returns:
                if move.state == 'done':
                    if move.product_uom != line.product_uom:
                        total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    else:
                        total -= move.product_uom_qty
            line.qty_received = total

    @api.multi
    def show_line_info(self):
        #Comentado por si no vale la solucion
        #view_id = self.env.ref('jim_purchase.purchase_order_form_line_info').id

        return {
            'name': _('Show info line Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.line',
            #'views': [(view_id, 'form')],
            #'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }

    def _onchange_quantity(self):
        if self.price_unit == 0.0:
            return super(PurchaseOrderLine,self)._onchange_quantity()
        else:
            # Llamamos a super para realizar el resto de cambios pero
            # volvemos a cambiar el precio.
            price_unit = self.price_unit
            res = super(PurchaseOrderLine,self)._onchange_quantity()
            self.price_unit = price_unit
            return res

    @api.multi
    def _prepare_stock_moves_bis(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        ### DROPSHIPPING CANCELADO ###
        for procurement in self.procurement_ids.filtered(lambda p: p.state == 'cancel' and p.rule_id.id == 141):
            procurement.reset_to_confirmed()
        return super(PurchaseOrderLine, self)._prepare_stock_moves(picking)


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.model
    def _default_picking_type(self):
        domain_wh = [('partner_id', '=', self.env.user.company_id.partner_id.id)]
        warehouse_id = self.env['stock.warehouse'].search(domain_wh, limit=1)
        types = warehouse_id and warehouse_id.in_type_id
        if not types:
            return super(PurchaseOrder, self)._default_picking_type()
        return types[:1]

    order_volume = fields.Float("Volume", compute="_compute_dimensions")
    order_weight = fields.Float("Weight", compute="_compute_dimensions")
    expediente = fields.Char("Expediente")
    picking_type_id = fields.Many2one('stock.picking.type',
                                      'Picking Type', required=True,
                                      default=_default_picking_type)

    @api.depends('order_line.line_volume', 'order_line.line_weight')
    def _compute_dimensions(self):
        for order in self:
            order_volume = 0.00
            order_weight = 0.00
            for line in order.order_line:
                order_volume += line.line_volume
                order_weight += line.line_weight
            order.update({
                'order_volume': order_volume,
                'order_weight': order_weight,
            })

    @api.multi
    def show_line_info(self):
        view_id = self.env.ref('jim_purchase.purchase_order_form_line_info').id

        return {
            'name': _('Show info line Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }

    @api.multi
    def _add_supplier_to_product(self):
        # Evitamos añadir el proveedor al producto o cambiar el precio, se hace
        # en la factura
        pass

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order.date_order = fields.Datetime.now()
        return super(PurchaseOrder, self).button_confirm()

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        if self.group_id:
            res['partner_id'] = self.group_id.partner_id.id
        return res


    @api.multi
    def action_view_picking(self):
        ## Sobre escribo toda la función para que recupere todos los alabranes en vez no coger los cancelados
        pick_ids = self.env['stock.picking']
        for order in self:
            for line in order.order_line:
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pick_ids |= moves.mapped('picking_id')
        action = self.env.ref('stock.action_picking_tree')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        pick_ids = sum([pick_ids.ids], [])
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result

    @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        for order in self:
            min_date = False
            for line in order.order_line:
                if not min_date or line.date_planned < min_date:
                    min_date = line.date_planned
            order.date_planned = min_date or order.date_order

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def action_add_purchase_invoice_wzd(self):

        if not self:
            return
        if not self.id:
            return
        if not self.partner_id:
            return
        ctx = dict(self._context.copy())
        ctx.update({'partner_id': self.partner_id.id})
        wizard_obj = self.env['purchase.invoice.wzd'].with_context(ctx)
        res_id = wizard_obj.create({'partner_id': self.partner_id.id,
                                    'account_invoice_id': self.id})
        return {
            'name': wizard_obj._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wizard_obj._name,
            'domain': [],
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id.id,
            'nodestroy': True,
        }

    @api.one
    def compute_amount(self):
        self._compute_amount()
