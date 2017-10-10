# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class StockMove(models.Model):


    _inherit = 'stock.move'

    def move_recheck_availability(self):
        move = self[0]

        if move.picking_id.state == 'cancel':
            move.picking_id.state = 'waiting'

        if move.picking_id.state not in ('waiting', 'confirmed', 'partially_available'):
            raise ValidationError(_('Pick state incorrect'))

        if move.state in ('cancel'):
            move.state = 'confirmed'

        elif move.state in ('waiting', 'assigned'):
            move.action_assign()

        elif move.state in ('confirmed'):
                move.force_assign()

    def move_force_availability(self):
        move = self[0]
        if move.picking_id.state not in ('waiting', 'confirmed', 'partially_available'):
            raise ValidationError(_('Pick state incorrect'))
        if move.state in ('confirmed', 'waiting', 'assigned'):
            move.force_assign()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_type', 'launch_pack_operations', 'move_lines.state', 'move_lines.picking_id',
                 'move_lines.partially_available')
    @api.one
    def _compute_state(self):
        super(StockPicking, self)._compute_state()
        if self.move_lines and \
                any(move.state == 'assigned' for move in self.move_lines) and \
                any(move.state in ('cancel', 'partially_available') for move in self.move_lines):
            self.state = 'partially_available'