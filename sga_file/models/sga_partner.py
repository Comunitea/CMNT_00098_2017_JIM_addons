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
    sga_outbound_priority = fields.Integer('Outbound Priority', required=True, default=50)
    sga_addr_name = fields.Char('Address Name', size=255)
    sga_active_fusion = fields.Boolean('Activer Fusion', required=True, default=False)

    @api.multi
    def new_mecalux_file(self):
        ids = [x.id for x in self]
        print ids
        new_sga_file = self.env['sga.file'].check_sga_file('res.partner', ids, code='ACC')

        return True

    @api.model
    def get_sga_line(self, type='ACC', version='04'):
        if type=='ACC' and version=='04':
            line = (u'%s%s%s%s%s%s%s%s%s')%(self.sga_operation, self.sga.account_code.rjust(12), self.name.rjust(80),
                              self.sga_outbound_priority.rjust(80), self.sga_addr_name.rjust(255),self.sga_white_space.rjust(""),
                                      self.sga_active_fusion.rjust(1), self.sga_atribute.rjust(20), self.sga_line_number.rjust(10))
        else:
            return False