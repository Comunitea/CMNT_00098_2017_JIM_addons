# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo import models, fields, exceptions, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import odoo.addons.decimal_precision as dp

PROCESS_STAGE = 20
DONE_STAGE = 30
NEW_STAGE = 1

class ClaimMakePicking(models.TransientModel):

    _inherit = 'claim_make_picking.wizard'

    @api.returns('stock.location')
    def _get_common_dest_location_from_line(self, lines):

        dest_loc = super(ClaimMakePicking, self)._get_common_dest_location_from_line(lines)
        if not len(dest_loc) and lines:
            dest_loc = lines[0].claim_id.warehouse_id.lot_stock_id
        return dest_loc


    @api.returns('res.partner')
    def _get_common_partner_from_line(self, lines):
        """ If all the lines have the same warranty return partner return that,
        else return an empty recordset
        """
        if lines[0].claim_id.ic:
            return lines[0].product_id.company_id.partner_id
        partners = lines.mapped('warranty_return_partner')
        partners = list(set(partners))
        return partners[0] if len(partners) == 1 else self.env['res.partner']



    def _get_picking_data(self, claim, picking_type, partner_id):

        if claim.claim_type.type == "customer":
            picking_type_orig = claim.warehouse_id.rma_in_type_id
        elif claim.claim_type.type == 'supplier':
            picking_type_orig = claim.warehouse_id.rma_out_type_id
        else:
            picking_type_orig = claim.warehouse_id.rma_int_type_id

        res = super(ClaimMakePicking, self)._get_picking_data(claim, picking_type, partner_id)
        picking_type = self._context.get('picking_type', False)
        res['origin'] = claim.code
        res['picking_type_id'] = picking_type_orig.id
        res['priority'] = "2"
        if picking_type == 'in':
            res['priority'] = "0"
            res['partner_id'] = claim.partner_id.id
            res['action_done_bool'] = True
            res['location_dest_id'] = claim.warehouse_id.lot_rma_id.id

        return res



    def _get_picking_line_data(self, claim, picking, line):

        res = super(ClaimMakePicking, self)._get_picking_line_data(claim, picking, line)
        picking_type = self._context.get('picking_type', False)
        if picking_type == 'in':
            res['location_dest_id'] = claim.warehouse_id.lot_rma_id.id
        res['claim_line_id'] = line.id

        return res


    def do_picks(self, claim_ids):

        domain = [('claim_id', 'in', claim_ids)]
        lines = self.env['claim.line'].search(domain)
        loc_ids = lines.mapped('location_dest_id')

        domain = [('claim_id', 'in', claim_ids),
                  ('location_dest_id', 'in', loc_ids.ids)]
        picks = self.env['stock.picking'].search(domain, order='id asc')

        picks_to_assign = picks.filtered(lambda x: x.state == 'confirmed' and x.location_dest_id.usage == 'internal')
        if picks_to_assign:
            picks_to_assign.action_assign()

        picks_to_force = picks.filtered(lambda x: x.state in ['partially_available', 'confirmed'] and x.location_dest_id.usage == 'internal')

        if picks_to_force:
            picks_to_force.force_assign()
        #picks_to_do = picks.filtered(lambda x: x.state == 'assigned' and x.action_done_bool)
        #for pick in picks_to_do:
        #    pick.do_transfer()

    def _create_picking(self, claim, picking_type):

        if not claim.stage_id.default_new:
            raise exceptions.UserError(_('Claim in incorrect stage'))
        claim.claim_line_ids.filtered(lambda x: x.state == 'draft').write({'state': 'confirmed'})
        if not claim.claim_line_ids.filtered(lambda x:x.state == 'confirmed'):
            raise exceptions.UserError(_('Not claim lines confirmed'))

        ctx = self._context.copy()

        ctx.update(picking_type=picking_type)
        claim_ids = []
        res = super(ClaimMakePicking, self.with_context(ctx))._create_picking(claim, picking_type)

        if claim.company_id != self.env.user.company_id:
            stock_pick_ids = claim.sudo().create_RMA_to_stock_pick()
        else:
            stock_pick_ids = claim.create_RMA_to_stock_pick()

        claim_ids += [claim.id]
        if not claim.ic and not claim.company_id.no_ic:
            claim_ic_ids = claim.create_IC_RMA()
            if claim_ic_ids:
                claim_ids += claim_ic_ids.ids


        self.sudo().do_picks(claim_ids)
        self.env['crm.claim'].browse(claim_ids).write({'stage_id': claim._stage_find(domain=[('default_run','=',True)])})
        claim.claim_line_ids.write({'state': 'treated'})

        return res


