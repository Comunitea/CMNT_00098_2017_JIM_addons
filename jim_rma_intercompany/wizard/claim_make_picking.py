# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo import models, fields, exceptions, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT

class ClaimMakePicking(models.TransientModel):

    _inherit = 'claim_make_picking.wizard'

    @api.returns('stock.location')
    def _get_common_dest_location_from_line(self, lines):

        dest_loc = super(ClaimMakePicking, self)._get_common_dest_location_from_line(lines)
        if not len(dest_loc) and lines:
            dest_loc = lines[0].claim_id.warehouse_id.lot_stock_id
        return dest_loc


    def _get_picking_data(self, claim, picking_type, partner_id):
        res = super(ClaimMakePicking, self)._get_picking_data(claim, picking_type, partner_id)
        picking_type = self._context.get('picking_type', False)
        res['origin'] = claim.name
        if picking_type == 'in':
            res['location_dest_id'] = claim.warehouse_id.lot_rma_id.id
            res['picking_type_id'] = claim.warehouse_id.rma_in_type_id.id
        return res



    def _get_picking_line_data(self, claim, picking, line):

        res = super(ClaimMakePicking, self)._get_picking_line_data(claim, picking, line)
        picking_type = self._context.get('picking_type', False)
        if picking_type == 'in':
            res['location_dest_id'] = claim.warehouse_id.lot_rma_id.id

        return res


    def do_picks(self, claim_ids):

        domain = [('claim_id', 'in', claim_ids)]
        picks = self.env['stock.picking'].search(domain)

        picks_to_assign = picks.filtered(lambda x: x.state == 'confirmed')
        picks_to_assign.action_assign()

        picks_to_force = picks.filtered(lambda x: x.state in ['waiting', 'partially_available', 'confirmed'])
        picks_to_force.force_assign()

        picks_to_do = picks.filtered(lambda x: x.state == 'assigned' and x.note !="RMA picking stock")
        for pick in picks_to_do:
            pick.do_transfer()

    def _create_picking(self, claim, picking_type):

        claim.claim_line_ids.filtered(lambda x: x.state == 'draft').write({'state': 'confirmed'})

        if not claim.claim_line_ids.filtered(lambda x:x.state == 'confirmed'):
            raise exceptions.UserError(_('Not claim lines confirmed'))

        ctx = self._context.copy()

        ctx.update(picking_type=picking_type)
        claim_ids = []
        res = super(ClaimMakePicking, self.with_context(ctx))._create_picking(claim, picking_type)

        if claim.company_id != self.env.user.company_id:
            pick_ids = claim.sudo().create_RMA_to_stock_pick()
        else:
            pick_ids = claim.create_RMA_to_stock_pick()

        claim_ids += [claim.id]
        if not claim.ic:
            claim_ic_ids = claim.create_IC_RMA()
            if claim_ic_ids:
                claim_ids += claim_ic_ids.ids


        self.sudo().do_picks(claim_ids)

        return res


