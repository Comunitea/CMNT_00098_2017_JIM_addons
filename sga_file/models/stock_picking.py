# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

class StockPickingTypeSGA(models.Model):

    _inherit = "stock.picking.type"

    sga_integrated = fields.Boolean('SGA Integrated', help = "If checked, odoo export this pick type to Mecalux")

class StockPickingSGAType(models.Model):

    _name = "stock.picking.sgatype"
    _rec_name = "code"

    code = fields.Char("Sale order type code", size=30)
    description = fields.Char("Sale order type description", size=100)

class StockPackOperationSGA(models.Model):

    _inherit = "stock.pack.operation"

    product_code = fields.Char(related="product_id.product_tmpl_id.default_code")
    uom_code = fields.Char(related="product_uom_id.sga_uom_base_code")
    line_number = fields.Integer("Number line")


class StockPickingSGA(models.Model):

    _inherit = "stock.picking"

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='A')
    warehouse_id = fields.Many2one(related="picking_type_id.warehouse_id")
    warehouse_code = fields.Char(related="picking_type_id.warehouse_id.code")

    code = fields.Char("Sale order type code", size=30)
    description = fields.Char("Sale order type description", size=100)

    stock_picking_sgatype_id = fields.Many2one('stock.picking.sgatype')
    stock_picking_sgatype_code = fields.Char(related="stock_picking_sgatype_id.code")
    stock_picking_sgatype_description = fields.Char(related="stock_picking_sgatype_id.description")

    sga_priority = fields.Integer("Priority", defatult=100)
    account_code = fields.Char(related="partner_id.ref")
    delivery_inst = fields.Char("Delivery warnings", size=255)
    verify_stock = fields.Boolean("Verify Stock", default=0)
    sga_company = fields.Char(related="partner_id.name")

    @api.multi
    def new_mecalux_file(self):

        ids = []
        for pick in self:
            if pick.picking_type_id.sga_integrated:
                ids.append(pick.id)
        if not ids:
            raise ValidationError("No picks to export to Mecalux")

        new_sga_file = self.env['sga.file'].check_sga_file('stock.picking', ids, code='PRE')
        return True

    @api.multi
    def do_transfer(self):
        res = super(StockPickingSGA, self).do_transfer()
        for pick in self:
            cont = 1
            for op in pick.pack_operation_product_ids:
                op.line_number = cont
                cont += 1
        return res

