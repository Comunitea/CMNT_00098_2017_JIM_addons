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
    sga_state = fields.Selection([(1, 'Actualizado'), (0, 'Pendiente actualizar'), (2, 'Baja')],
                                 default=False,
                                 help="Estado integracion con mecalux")

    @api.multi
    def toggle_active(self):
        res = super(ResPartnerSGA, self).toggle_active()
        for record in self:
            if record.active:
                operation = "F"
            else:
                operation = "B"
            record.new_mecalux_file(operation=operation)
            record.sga_state = 1



    @api.multi
    def write(self, values):
        res = super(ResPartnerSGA, self).write(values)
        fields_to_check = ('ref', 'sga_outbound_priority', 'name',
                           'sga_material_abc_code', 'sga_change_material_abc',
                           'uom_id', 'name', 'sga_prod_shortdesc', 'packaging_ids')
        fields = sorted(list(set(values).intersection(set(fields_to_check))))
        if fields:
            self.sga_state = 0
            icp = self.env['ir.config_parameter']
            if icp.get_param('product_auto'):
                self.new_mecalux_file(operation="F")
                self.sga_state = 1
        return res



    @api.model
    def create(self, values):
        values['sga_state'] = 0
        res = super(ResPartnerSGA, self).create(values)
        icp = self.env['ir.config_parameter']
        if icp.get_param('product_auto'):
            res.new_mecalux_file(operation="A")
            res.sga_state = 1
        return res

    @api.multi
    def new_mecalux_file(self, operation=False):
        try:
            ids = [x.id for x in self]
            ctx = dict(self.env.context)
            if operation:
                ctx['operation'] = operation
            if 'operation' not in ctx:
                ctx['operation'] = 'F'
            new_sga_file = self.env['sga.file'].with_context(ctx).check_sga_file('res.partner', ids, code='ACC')
            self.write({'sga_state': 1})
            return True
        except:
            self.write({'sga_state': 0})
            return False
