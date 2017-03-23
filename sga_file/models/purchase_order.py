# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re


class PurchaseOrderLineSGA (models.Model):

    _inherit ="purchase.order.line"

    product_code = fields.Char(related="product_id.product_tmpl_id.default_code")
    uom_code = fields.Char(related="product_uom.sga_uom_base_code")
    line_number = fields.Integer("Number line")


class PurchaseOrderSGA(models.Model):

    _inherit = "purchase.order"

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='A')
    #warehouse_code = fields.Char(related="warehouse_id.code")

    @api.multi
    def new_mecalux_file(self):

        ids = [x.id for x in self]
        print ids
        new_sga_file = self.env['sga.file'].check_sga_file('purchase.order', ids, code='PRE')
        return True
