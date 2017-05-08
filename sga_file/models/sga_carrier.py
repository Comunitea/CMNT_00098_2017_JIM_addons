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

    carrier_code = fields.Char("Carrier Code", required=True, size=20, help ="SGA code to mecalux")
    description = fields.Char("Description")
    contact = fields.Char("Contact")
    sga_state = fields.Selection([(1, 'Actualizado'), (0, 'Pendiente actualizar')],
                                 default=0,
                                 help="Estado integracion con mecalux")

    _sql_constraints = [
        ('carrier_code_uniq', 'unique (carrier_code)', "Carrier code already exists !"),
    ]


    @api.onchange('description', 'contact', 'name')
    def onchange_carrier(self):
        for categ in self:
            categ.sga_state = 0

    @api.multi
    def write(self, values):
        #return super(DeliveryCarrierSGA, self).write(values)

        #lanza un write en product. Revisar
        values['sga_state'] = 1
        res = super(DeliveryCarrierSGA, self).write(values)

        fields_to_check = ('description', 'contact', 'name', 'carrier_code')
        fields = list(set(values).intersection(set(fields_to_check)))

        if fields:
            icp = self.env['ir.config_parameter']
            if icp.get_param('product_auto'):
                res_sga = self.export_delivery_carrier_to_mecalux(operation="F")
                if not res_sga:
                    self.sga_state = 0
        return res

    @api.model
    def create(self, values):
        #return super(DeliveryCarrierSGA, self).create(values)
        # lanza un write en product. Revisar
        values['sga_state'] = 1
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
            self.write({'sga_state': res})
        return res