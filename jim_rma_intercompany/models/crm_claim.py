# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models

class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    def check_picking_moves(self):
        for move in self.claim_line_ids.filtered(lambda x:x.state == 'in_to_treate'):
            if move.move_int_id.state == 'done':
                move.state = 'treated'
            elif move.move_int_id.state == 'cancel':
                move.state = 'draft'

    def get_scrap_location(self):
        domain = [('scrap_location', '=', True)]
        scrap_loc = self.env['stock.location'].search(domain)
        return scrap_loc and scrap_loc[0] or False

    def get_rma_location(self, warehouse_id=False):
        if warehouse_id and warehouse_id.lot_rma_id:
            return warehouse_id.lot_rma_id
        domain = [('return_location', '=', True)]
        return_loc = self.env['stock.location'].search(domain)
        return return_loc and return_loc[0] or False

    @api.onchange('claim_line_ids')
    def set_stage_id(self):
        if all((x.state == 'refused' or x.state == 'treated') for x in self.claim_line_ids):
            state = 50
        elif all(x.state == 'draft' for x in self.claim_line_ids):
            state = 1
        else:
            state = 10
        self.stage_id = self.stage_find(False, [('sequence','=',state)])

    @api.model
    def create(self, vals):
        """Return write the identify number once the claim line is create.
        """
        if vals.get('company_id', False) == 4:
            raise exceptions.ValidationError(
                    _('Not allowed company.')
                )
        res = super(CrmClaim, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('company_id', False) == 4:
            raise exceptions.ValidationError(
                _('Not allowed company.')
            )
        res = super(CrmClaim, self).write(vals)
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        delivery_address_id = self.partner_id.child_ids.filtered(lambda x:x.type == 'delivery')
        if len(delivery_address_id)>0:
            self.delivery_address_id = delivery_address_id[0]
        else:
            self.delivery_address_id = self.partner_id



class ClaimLine(models.Model):
    _inherit = "claim.line"

    move_int_id = fields.Many2one('stock.move',
                                 string='Move Line from picking int',
                                 help='The move line related'
                                      ' to the stocked/scraped product')
    state = fields.Selection(default='confirmed')

    @api.model
    def create(self, vals):
        """Return write the identify number once the claim line is create.
        """
        vals = vals or {}
        if not vals.get('location_dest_id', False):
            claim_id = self.env['crm.claim'].browse(vals.get('claim_id'))
            vals['location_dest_id'] = claim_id.warehouse_id.lot_stock_id.id

        res = super(ClaimLine, self).create(vals)
        return res




