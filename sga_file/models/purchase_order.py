# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _create_picking(self):
        res = super(PurchaseOrder, self)._create_picking()

        StockPicking = self.env['stock.picking']
        for order in self:
            pickings = order.picking_ids.filtered(lambda x:
                                                  x.state not in ('done', 'cancel') and
                                                  x.picking_type_id.sga_integrated)

            for pick in pickings:
                if pick.new_mecalux_file():
                    pick.sga_state = 'PM'