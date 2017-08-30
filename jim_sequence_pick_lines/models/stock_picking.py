# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from openerp import models, api


from odoo import models, api, fields



class StockMove(models.Model):
    _inherit = 'stock.move'
    _order = 'picking_id, template_sequence, sequence, id'

    template_sequence = fields.Integer()

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        res = super(StockMove, self)._get_invoice_line_vals(move,
                                                            partner,
                                                            inv_type)
        res.update({'sequence':  move.sequence,
                   'template_sequence': move.template_sequence})

        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_lines')
    def _get_max_line_sequence(self):
        for picking in self:
            picking.max_line_sequence = (
                max(picking.mapped('move_lines.sequence')) + 1000
                )

    max_line_sequence = fields.Integer(string='Max sequence in lines', compute='_get_max_line_sequence')

