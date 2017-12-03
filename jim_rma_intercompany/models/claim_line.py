# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp

class ClaimLine(models.Model):

    _inherit = 'claim.line'


    @api.multi
    def get_qty_done(self):
        for line in self:
            moves = self.picking_ids.mapped('move_lines').filtered(
                lambda x:x.claim_line_id == line.id and
                         (x.location_id in ('customer', 'supplier') or x.location_dest_id in ('customer', 'supplier')))

    move_int_id = fields.Many2one('stock.move',
                                  string='Move from RMA',
                                  help='The move line related'
                                       ' to the stocked/scraped product')
    #invoice_line_id = fields.Many2one('account.invoice.line', string="Invoice line")
    claim_line_id = fields.Many2one('claim.line')
    #sobreescribo para quitar opciones y mejorar descripcion de los estados
    state = fields.Selection(default='confirmed')



    @api.model
    def create(self, vals):
        vals = vals or {}
        if not vals.get('location_dest_id', False):
            claim = self.env['crm.claim'].browse([vals.get('claim_id', False)])
            vals['location_dest_id'] = claim.warehouse_id.lot_stock_id.id
        res = super(ClaimLine, self).create(vals)
        return res

    @api.returns('stock.location')
    def get_destination_location(self, product_id, warehouse_id):
        """ Compute and return the destination location to take
        for a return. Always take 'Supplier' one when return type different
        from company.
        """
        return self.location_dest_id or warehouse_id.lot_stock_id
