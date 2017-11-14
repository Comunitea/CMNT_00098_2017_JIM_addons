# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

class ClaimLine(models.Model):

    _inherit = 'claim.line'

    move_int_id = fields.Many2one('stock.move',
                                  string='Move from RMA',
                                  help='The move line related'
                                       ' to the stocked/scraped product')
    #invoice_line_id = fields.Many2one('account.invoice.line', string="Invoice line")

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
