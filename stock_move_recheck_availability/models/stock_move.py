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
            move.picking_id.state = 'confirmed'

        if move.picking_id.state not in ('waiting', 'confirmed', 'partially_available'):
            raise ValidationError(_('Pick state incorrect'))

        if move.state in ('cancel'):
            move.state = 'waiting'

        if move.state in ('waiting', 'confirmed', 'assigned'):
            move.action_assign()

        if move.state == 'confirmed':
            move.force_assign()

