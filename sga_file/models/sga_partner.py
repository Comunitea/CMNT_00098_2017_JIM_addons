# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re


class ResPartnerSGA(models.Model):
    _inherit = "res.partner"

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='F')
    sga_outbound_priority = fields.Integer('Outbound Priority', default=50)
    sga_addr_name = fields.Char('Address Name', size=255)
    sga_active_fusion = fields.Selection([('1', 'True'), ('0', 'False')], 'Active Fusion', default='0')

    @api.multi
    def new_mecalux_file(self):
        ids = [x.id for x in self]
        print ids
        new_sga_file = self.env['sga.file'].check_sga_file('res.partner', ids, code='ACC')

        return True
