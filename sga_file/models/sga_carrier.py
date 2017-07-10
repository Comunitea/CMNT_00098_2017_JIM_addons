# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

SGA_STATE = [('AC', 'Actualizado'), ('PA', 'Pendiente actualizar'), ('BA', 'Baja'), ('ER', 'Error')]


class DeliveryCarrierSGA(models.Model):

    # TODO res.partner with carrier = True ????????????????'

    _inherit = "delivery.carrier"

    carrier_code = fields.Char("Carrier Code", required=True, size=20, help ="SGA code to mecalux")
    description = fields.Char("Description")
    contact = fields.Char("Contact")
    sga_state = fields.Selection(SGA_STATE,
                                 default='PA',
                                 help="Estado integracion con mecalux")

    _sql_constraints = [
        ('carrier_code_uniq', 'unique (carrier_code)', "Carrier code already exists !"),
    ]


    @api.onchange('description', 'contact', 'name')
    def onchange_carrier(self):
        for categ in self:
            categ.sga_state = 'PA'

    @api.multi
    def write(self, values):
        #return super(DeliveryCarrierSGA, self).write(values)

        #lanza un write en product. Revisar
        values['sga_state'] = 'AC'
        res = super(DeliveryCarrierSGA, self).write(values)

        fields_to_check = ('description', 'contact', 'name', 'carrier_code')
        fields = list(set(values).intersection(set(fields_to_check)))

        if fields:
            icp = self.env['ir.config_parameter']
            if icp.get_param('product_auto'):
                res_sga = self.export_delivery_carrier_to_mecalux(operation="F")
                if not res_sga:
                    self.sga_state = 'ER'
        return res

    @api.model
    def create(self, values):
        #return super(DeliveryCarrierSGA, self).create(values)
        # lanza un write en product. Revisar
        values['sga_state'] = 'AC'
        res = super(DeliveryCarrierSGA, self).create(values)
        icp = self.env['ir.config_parameter']
        if icp.get_param('product_auto'):
            res.export_delivery_carrier_to_mecalux(operation="F")

        return res

    @api.multi
    def export_delivery_carrier_to_mecalux(self, operation=False):
        try:
            ids = [x.id for x in self]
            ctx = dict(self.env.context)
            if operation:
                ctx['operation'] = operation
            if 'operation' not in ctx:
                ctx['operation'] = 'F'
            new_sga_file = self.env['sga.file'].with_context(ctx).check_sga_file('delivery.carrier', ids, code='CAR')
            res = 1
        except:
            print "Error al exportar carrier a Mecalux"
            res = 0

        if not res:
            self.write({'sga_state': 'ER'})
        return res