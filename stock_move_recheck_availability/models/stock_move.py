# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class StockMove(models.Model):


    _inherit = 'stock.move'

    def move_recheck_availability(self):

        move = self[0]
        if move.state in ('cancel', 'waiting'):
            move.state='waiting'

        if move.state=='waiting':
            move.action_assign()
        elif move.state=='confirmed':
            move.force_assign()

