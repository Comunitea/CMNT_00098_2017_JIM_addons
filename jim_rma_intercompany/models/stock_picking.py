# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        for pick in self:
            if pick.claim_id:
                pick.claim_id.check_picking_moves()
        return res
