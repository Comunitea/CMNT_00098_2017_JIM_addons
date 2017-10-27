# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class ClaimLineScrapWzd(models.TransientModel):

    _name = 'claim_line.scrap.wizard'
    _description = 'Wizard to create scrap/stock moves from claim lines'

    @api.one
    @api.depends('new_qty_to_scrap')
    def _get_new_qty(self):
        self.new_qty_to_stock = self.product_returned_quantity - self.new_qty_to_scrap


    claim_line_id = fields.Many2one('claim.line')
    number = fields.Char(related='claim_line_id.number')
    display_name = fields.Char(related='claim_line_id.display_name')
    product_id = fields.Many2one(related='claim_line_id.product_id')
    product_returned_quantity = fields.Float(related='claim_line_id.product_returned_quantity')
    new_qty_to_scrap = fields.Float('Quantity to scrap', digits=(12, 2),
                     help="Quantity of product returned")
    new_qty_to_stock = fields.Float('Quantity to scrap', digits=(12, 2),
                                    help="Quantity of product returned - scraped",
                                    compute="_get_new_qty")

    def action_refresh_lines(self):
        if self.new_qty_to_scrap:
            new_claim_line = self.claim_line_id.copy()
            self.claim_line_id.product_returned_quantity = self.new_qty_to_stock
            new_claim_line.product_returned_quantity = self.new_qty_to_scrap
            scrap_loc = self.claim_line_id.claim_id.get_scrap_location()
            if not scrap_loc:
                raise ValidationError(_('Scrap location not found'))
            new_claim_line.location_dest_id = scrap_loc[0]
            new_claim_line.state = 'in_to_control'
            new_claim_line.claim_diagnosis = 'damaged'
            new_claim_line.move_in_id = self.claim_line_id.move_in_id

            view_id = self.env['ir.ui.view'].search(
                [('model', '=', 'crm.claim'),
                 ('type', '=', 'form')])[0]
            return {

                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id.id,
                'res_model': 'crm.claim',
                'res_id': self.claim_line_id.claim_id.id,
                'type': 'ir.actions.act_window',
            }

    @api.model
    def default_get(self, fields):
        rec = super(ClaimLineScrapWzd, self).default_get(fields)
        claim_line_id_id = self._context.get('active_id', False)
        claim_line_id = self.env['claim.line'].browse(claim_line_id_id)
        rec['claim_line_id'] = claim_line_id.id
        if claim_line_id.location_dest_id.scrap_location:
            raise ValidationError(_('This is a scrap location!!!'))
        return rec