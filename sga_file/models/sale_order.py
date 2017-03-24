# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

class SaleOrderType (models.Model):

    _name = "sale.order.type"
    _rec_name = "code"

    code = fields.Char("Sale order type code", size=30)
    description = fields.Char("Sale order type description", size=100)


class SaleOrderLineSGA (models.Model):

    _inherit ="sale.order.line"

    product_code = fields.Char(related="product_id.product_tmpl_id.default_code")
    uom_code = fields.Char(related="product_uom.sga_uom_base_code")
    sga_comment = fields.Char("Comment", size=255)

class SaleOrderSGA(models.Model):

    #

    _inherit = "sale.order"

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='A')
    warehouse_code = fields.Char(related="warehouse_id.code")
    sale_order_type_id = fields.Many2one('sale.order.type')
    sale_order_type_code = fields.Char(related="sale_order_type_id.code")
    sale_order_type_description = fields.Char(related="sale_order_type_id.description")
    sga_priority = fields.Integer("Priority", defatult=100)
    account_code = fields.Char(related="partner_id.ref")
    delivery_inst = fields.Char("Delivery warnings", size=255)
    verify_stock = fields.Boolean("Verify Stock", default=0)





    @api.multi
    def new_mecalux_file(self):

        ids = [x.id for x in self]
        print ids
        new_sga_file = self.env['sga.file'].check_sga_file('sale.order', ids, code='SOR')
        return True
