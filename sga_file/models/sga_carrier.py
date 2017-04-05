# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re


class DeliveryCarrierSGA(models.Model):

    # TODO res.partner with carrier = True ????????????????'

    _inherit = "delivery.carrier"

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='F')
    carrier_code = fields.Char("Carrier Code", required=True, size=20, help ="SGA code to mecalux")
    description = fields.Char("Description")
    contact = fields.Char("Contact")

    _sql_constraints = [
        ('carrier_code_uniq', 'unique (carrier_code)', "Carrier code already exists !"),
    ]

    @api.multi
    def export_mecalux_file(self):
        ids = [x.id for x in self]
        print ids
        new_sga_file = self.env['sga.file'].check_sga_file('delivery.carrier', ids, code='CAR')
        return True
