# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models, fields, exceptions, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT

RMA_STATE_IN = ('confirmed')
RMA_STATE_INT = ('in_to_control')

class ClaimMakePicking(models.TransientModel):
    _inherit = 'claim_make_picking.wizard'

    @api.model
    def _default_claim_line_source_location_id(self):
        picking_type = self.env.context.get('picking_type')
        if picking_type == 'in':
            res = super(ClaimMakePicking, self)._default_claim_line_source_location_id()
        elif picking_type == 'int':
            res = self.claim_id.get_rma_location()
        else:
            res = False
        return res


    dest_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Destination Warehouse',
        default=lambda self: self.env.context.get('warehouse_id'),
        help="Warehouse where to receipt products from customers.",
    )
    to_scrap = fields.Boolean(string="To scrap", default=False)
    claim_id = fields.Many2one('crm.claim')
    claim_line_source_location_id = fields.Many2one(
        'stock.location', string='Source Location',
        default=_default_claim_line_source_location_id,
        help="Location where the returned products are from.")

    @api.model
    def default_get(self, fields):
        rec = super(ClaimMakePicking, self).default_get(fields)
        rec['claim_id'] = self._context.get('active_id', False)
        return rec


    @api.multi
    def action_create_picking(self):

        self.refresh_lines()
        if not self.claim_line_ids:
            raise exceptions.UserError(
                _('Not lines to create a pick')
            )

        picking_type = self.env.context.get('picking_type')
        res = super(ClaimMakePicking, self.sudo()).action_create_picking()
        if picking_type == 'in':
            purchase_ids = self.sudo().create_purchase_order()
        return res

    def link_rma_moves_to_purchase(self, purchase_ids):
        claim_id = self.env.context['active_id']
        claim_id = self.env['crm.claim'].browse(claim_id)
        for pick in claim_id.picking_ids:
            claim_moves = pick.move_lines

        for purchase in purchase_ids:
            for pick in purchase.picking_ids:
                purchase_moves = pick.move_lines

        for move_p in purchase_moves:
            c_move = claim_moves.filtered(lambda x:x.product_id.id == move_p.product_id.id)
            #c_move.move_dest_id = move_p


    @api.multi
    def create_purchase_order(self):
        lines_to_IC = self.claim_line_ids.filtered(lambda x: x.product_id.company_id != self.claim_id.company_id)
        if not lines_to_IC:
            return []
        purchase_ids = []
        company_ids = [x.product_id.company_id for x in lines_to_IC]
        company_ids = list(set(company_ids))
        #print "Compañias para crear PO y SO >> %s\nPara la lines %s"%(company_ids, ["\n%s"%x.product_id for x in lines_to_IC])
        created_pickings_ic = self.env['stock.picking']
        ctx = self._context.copy()
        ctx.update(no_IC_sale_order=True)
        for company in company_ids:
            #reo una compra por cada compañia
            new_purchase = self.env['purchase.order'].new(self.get_purchase_order_vals(self.claim_id, company))
            new_purchase.onchange_partner_id()
            new_purchase_vals = new_purchase._convert_to_write(new_purchase._cache)
            purchase = self.env['purchase.order'].create(new_purchase_vals)

            #print"Order creada %s"%purchase.name
            new_lines = lines_to_IC.filtered(lambda x: x.product_id.company_id.id == company.id)
            for line in new_lines:
                new_purchase_line = self.env['purchase.order.line'].new(
                                    {'product_id': line.product_id.id,
                                    'order_id': purchase.id})
                new_purchase_line.onchange_product_id()
                new_purchase_line.product_qty = line.product_returned_quantity
                ic_price = line.product_id.get_intercompany_price(company.id, self.claim_id.company_id.partner_id.id)
                new_purchase_line.price_unit = ic_price
                new_purchase_line_vals = new_purchase_line._convert_to_write(new_purchase_line._cache)
                purchase.order_line.create(new_purchase_line_vals)

            purchase.button_confirm()
            purchase.group_id.claim_id = self.claim_id
            created_pickings_ic |= purchase.picking_ids

            order_ids = self.env['sale.order'].search([('auto_purchase_order_id', '=', purchase.id)])
            for order in order_ids:
                order.claim_id = self.claim_id.id
                order.picking_ids.force_assign()
                created_pickings_ic |= order.picking_ids
            purchase.picking_ids.do_transfer()
            created_pickings_ic.write({'note': self._get_picking_note(),
                                       'claim_id': self.claim_id.id})
            purchase_ids.append(purchase)
        return purchase_ids


    def get_purchase_order_vals(self, claim_id, company_id):
        purchase_to_partner = claim_id.company_id.partner_id
        picking_type = self.env['stock.picking.type'].search([('name', '=', 'DEV IC')])
        if not picking_type:
            raise exceptions.UserError(
                _('Picking type named "DEV IC" not created')
            )

        vals = {
            'partner_id': purchase_to_partner.id,
            'company_id': company_id.id,
            'intercompany': True,
            'origin': claim_id.code,
            'date_planned': fields.Datetime.now(),
            'picking_type_id': picking_type and picking_type.id,
            'claim_id': claim_id.id
            }
        return vals

    @api.onchange('to_scrap')
    def onchange_to_scrap(self):
        if self.dest_warehouse_id:
            if self.to_scrap:
                self.claim_line_dest_location_id = self.claim_id.get_scrap_location()
            else:
                self.claim_line_dest_location_id = self.dest_warehouse_id.lot_stock_id
        else:
            self.claim_line_dest_location_id = self._default_claim_line_dest_location_id()

    @api.onchange('dest_warehouse_id')
    def onchange_dest_warehouse_id(self):
        self.onchange_to_scrap()

    @api.onchange('claim_line_dest_location_id')
    def onchange_claim_line_dest_location_id(self):
        self.refresh_lines(self.get_domain())

    def refresh_lines(self, domain=[]):
        lines = self._default_claim_line_ids(domain)
        self.claim_line_ids = lines or False



    ##Sobreescribo la función completa para poder pasar un dominio previo y y un move_field
    @api.returns('claim.line')
    def _default_claim_line_ids(self, domain=[]):
        # TODO use custom states to show buttons of this wizard or not instead
        # of raise an error
        if not self.claim_line_dest_location_id:
            return self.env['claim.line']
        if not domain:
            domain = self.get_domain()
        picking_type = self.env.context.get('picking_type')
        move_field = 'move_%s_id'%picking_type
        domain += [('claim_id', '=', self.env.context['active_id'])]
        lines = self.env['claim.line']. \
            search(domain)
        if lines:
            domain = domain + ['|', (move_field, '=', False),
                               (move_field + '.state', '=', 'cancel')]
            lines = lines.search(domain)
            if not lines:
                raise exceptions.UserError(
                    _('A picking has already been created for this claim.')
                )
        else:
            lines = self.env['claim.line']
        return lines

    def get_picking_state_filter(self, picking_type=False):
        state = ''
        if not picking_type:
            picking_type = self.env.context.get('picking_type')
        if picking_type == 'in':
            state = RMA_STATE_IN
        elif picking_type == 'int':
            state = RMA_STATE_INT
        return state

    def get_domain(self, filter_state=True, dest_location=True):
        domain = []
        if filter_state:
            domain += [('state', '=', self.get_picking_state_filter(self._context.get('picking_type', False)))]
        if dest_location:
            domain += [('location_dest_id', '=', self.claim_line_dest_location_id.id)]
        return domain

    def _create_picking(self, claim, picking_type):

        partner_id = False
        if picking_type == 'in':
            picking_type = self.dest_warehouse_id.rma_in_type_id
            write_field = 'move_in_id'
            state = 'confirmed'
            auto = True

        elif picking_type == 'out':
            picking_type = self.dest_warehouse_id.rma_out_type_id
            write_field = 'move_out_id'
            state = 'confirmed'
            auto = False

        else:
            picking_type == 'int'
            picking_type = self.dest_warehouse_id.rma_int_type_id
            write_field = 'move_int_id'
            state = 'in_to_treate'
            auto = False
            partner_id = claim.company_id.partner_id.id

        if not partner_id:
            partner_id = claim.delivery_address_id.id and claim.delivery_address_id.id
        claim_lines = self.claim_line_ids
        #print"Proceso [%s] con %s"%(len(claim_lines), picking_type.name)
        # In case of product return, we don't allow one picking for various
        # product if location are different
        # or if partner address is different
        if self.env.context.get('product_return'):
            common_dest_location = self._get_common_dest_location_from_line(
                claim_lines)
            # if not common_dest_location:
            #     raise exceptions.UserError(
            #         _('A product return cannot be created for various '
            #           'destination locations, please choose line with a '
            #           'same destination location.')
            #     )

            claim_lines.auto_set_warranty()
            common_dest_partner = self._get_common_partner_from_line(
                claim_lines) or self.claim_id.partner_id
            if not common_dest_partner:
                raise exceptions.UserError(
                    _('A product return cannot be created for various '
                      'destination addresses, please choose line with a '
                      'same address.')
                )
            partner_id = common_dest_partner.id

        # create picking
        # tengo que crear tantos picking como comapñias distintas en las lineas de articulos
        companies = [claim.company_id.id]
        companies += [x.product_id.company_id.id for x in self.claim_line_ids if x.product_id.company_id != claim.company_id]
        pickings = self.env['stock.picking']
        companies = list(set(companies))
        #print"Compañias %s"%companies
        for company in companies:
            company_lines = claim_lines.filtered(lambda x:x.product_id.company_id.id == company)
            if len(company_lines) == 0:
                continue

            picking = self.env['stock.picking'].create(
                self._get_picking_data(claim, picking_type, partner_id, company))
            #print"Pick creado: %s"%picking.name
            # Create picking lines
            for line in company_lines:
                move = self.env['stock.move'].create(
                    self._get_picking_line_data(claim, picking, line, company))
                line.write({write_field: move.id,
                            'state': state})
            pickings |= picking
            #for pick in pickings:
            #print "%s, [%s]"%(pick.name, pick.state)
        if pickings:
            #print"Proceso los pickings %s"%pickings
            pickings.signal_workflow('button_confirm')
            pickings.action_assign()
            if auto:
                for pick in pickings:
                    pick.force_assign()
                    pick.do_transfer()
                self.claim_line_ids.write({'state': RMA_STATE_INT})

        #domain = ("[('picking_type_id', '=', %s), ('partner_id', '=', %s), ('company_id', '=', %s)]" %
        #          (picking_type.id, partner_id,self.env.user.company_id.id))
        #Devuelvo un pick asociado de esta compañia
        #print "Picking creados : %s"%len(pickings)
        domain = [('claim_id', '=', claim.id)]
        if self.env.user.company_id.parent_id:
            domain += [('company_id', '=', self.env.user.company_id.id)]

        view_id = self.env['ir.ui.view'].search(
            [('model', '=', 'stock.picking'),
             ('type', '=', 'form')])[0]
        return {
            'name': self._get_picking_name(),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'domain': domain,
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }

    def _get_picking_data(self, claim, picking_type, partner_id, company_id=False):

        res = super(ClaimMakePicking, self)._get_picking_data(claim, picking_type, partner_id)

        picking_type_ctx = self.env.context.get('picking_type')
        res['company_id'] = company_id or self.company_id.id
        if picking_type_ctx == 'in':
            if not self.dest_warehouse_id.lot_rma_id:
                raise exceptions.ValidationError(
                    _('Not rma location for this warehouse.')
                )
            res['location_dest_id'] = self.dest_warehouse_id.lot_rma_id.id
            self.claim_line_ids.write({'state': RMA_STATE_INT})

        elif picking_type_ctx == 'int':
            res['location_dest_id'] = self.claim_line_dest_location_id.id
            res['location_id'] = self.claim_id.get_rma_location() and self.claim_id.get_rma_location().id
            if self.claim_line_dest_location_id.scrap_location:
                res['picking_type_id'] = self.dest_warehouse_id.rma_out_type_id.id
            else:
                res['picking_type_id'] = self.dest_warehouse_id.rma_int_type_id.id

        else:
            if self.claim_line_dest_location_id.scrap_location:
                res['picking_type_id'] = self.dest_warehouse_id.rma_out_type_id.id
            else:
                res['picking_type_id'] = self.dest_warehouse_id.rma_int_type_id.id
            res['location_dest_id'] = self.claim_line_dest_location_id.id
            res['location_id'] = self.dest_warehouse_id.lot_rma_id.id
            self.claim_line_ids.write({'state': 'treated'})
        return res

    def _get_picking_line_data(self, claim, picking, line, company_id=False):

        picking_type = self.env.context.get('picking_type')
        res = super(ClaimMakePicking, self)._get_picking_line_data(claim, picking, line)
        res['company_id'] = company_id or self.company_id.id
        if picking_type == 'in':
            res['location_dest_id'] = self.dest_warehouse_id.lot_rma_id.id
        elif picking_type == 'int':
            res['location_dest_id'] = self.claim_line_dest_location_id.id
            res['location_id'] = self.claim_id.get_rma_location() and self.claim_id.get_rma_location().id
        else:
            res['location_dest_id'] = self.claim_line_dest_location_id.id
            res['location_id'] = self.dest_warehouse_id.lot_rma_id.id
        return res
