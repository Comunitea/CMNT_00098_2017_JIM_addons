# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re


class StockInventoryLineSGA(models.Model):

    _inherit = "stock.inventory.line"

    global_qty = fields.Float(
        'Global Quantity', compute='_compute_global_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True)

    global_product_qty = fields.Float(
        'Global Quantity', compute='_compute_global_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True)

    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_global_qty(self):
        if not self.product_id:
            self.global_qty = 0
        else:
            global_qty = sum([x.qty for x in self._get_quants_global()])
            if global_qty and self.product_uom_id and self.product_id.uom_id != self.product_uom_id:
                global_qty = self.product_id.uom_id._compute_quantity(global_qty, self.product_uom_id)
            self.global_qty = global_qty

    def _get_quants_global(self):
        return self.env['stock.quant'].search([
            ('location_id', '=', self.location_id.id),
            ('lot_id', '=', self.prod_lot_id.id),
            ('product_id', '=', self.product_id.id),
            ('owner_id', '=', self.partner_id.id),
            ('package_id', '=', self.package_id.id)])

    def _get_move_values(self, qty, location_id, location_dest_id):

        res = super(StockInventoryLineSGA, self)._get_move_values(qty, location_id, location_dest_id)
        # res['company_id'] = inventory_id.company_id.id >> move company ...
        res['company_id'] = self.company_id.id
        return res

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.company_id = self.product_id.company_id
        return super(StockInventoryLineSGA, self).onchange_product()

class StockInventorySGA(models.Model):

    _inherit = "stock.inventory"

    def get_stock_query_from_mecalux(self):
        file_id = self.env['sga.file'].process_sga_files(file_type='STO')

    def new_stock_query_to_mecalux(self):

        if not self.location_id.get_warehouse().sga_integrated:
            raise ValidationError ("Solo puedes consultar en stock en almacenes con Mecalux")

        if self.state != 'confirm':
            raise ValidationError("Solo puedes consultar inventarios con estado: 'En Proceso'")

        ids = [x.product_id.id for x in self.line_ids]
        new_sga_file = self.env['sga.file'].check_sga_file('product.product', ids, code='PST')
        return new_sga_file

    def import_inventory_STO(self, file_id):

        sga_file = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file.sga_file, 'r')
        sga_file_lines = sga_file.readlines()
        sga_file.close()
        stock_inv_pool = []
        loop = 0
        num_details = 0
        for line in sga_file_lines:
            if loop < num_details:
                loop += 1
                continue
            # Warehouse code
            st = 0
            en = 10
            warehouse_code = line[st:en].strip()

            # Product code
            st = en
            en += 50
            product_code = line[st:en].strip()

            # Empty fields
            st = en
            en += 50 + 50 + 14 + 12 + 50 + 14 + 14 + 20 + 50 + 12 + 3 + 50

            # quantity (int + dec >> float)
            st = en
            en += 7
            quantity_int = int(line[st:en])
            st = en
            en += 5
            quantity_dec = int(line[st:en]) / 5000
            quantity = quantity_int + quantity_dec

            # num_details >> M;ust be ignored make loop over num line and continue
            st = en
            en += 10
            num_details = int(line[st:en])
            loop = 0

            # busco todo el stock de ese product en ese almacen que no pertenezca a la compañia del producto

            product_id = self.env['product.product'].search([('default_code', '=', product_code)])
            if not product_id:
                raise ValidationError("Referencia no encontrada")

            company_id = product_id.company_id

            warehouse_id = self.env['stock.warehouse'].search([('code', '=', warehouse_code)])
            # POR SEGURIDAD
            if not warehouse_id.sga_integrated:
                raise ValidationError ("Solo almacenes con gestion SGA")

            if not warehouse_id:
                raise ValidationError("Codigo de almacen no encontrado")

            ctx = dict(product_id._context)
            location_id = warehouse_id.lot_stock_id

            ctx.update({'force_company': company_id.id, 'location_id': [location_id.id]})

            total_qties = product_id.sudo()._product_available()
            qty = total_qties[product_id.id]['qty_available']

            ## if quantity (from sga) == qty (from odoo)  --- All companys >> stock is ok >> no new inventory_line
            if quantity != qty:

                total_not_company_qties = product_id.with_context(ctx).sudo()._product_available()
                qty_comp = total_not_company_qties[product_id.id]['qty_available']

                # new line for product_id.company_id >>
                new_qty = quantity - (qty-qty_comp)
                new_line_vals = {
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'product_qty': new_qty,
                    'company_id': product_id.company_id.id
                }

                domain_stock_inv = [('product_id', '=', product_id.id), ('inventory_id.state', '=', 'confirm')]
                inv_line = self.env['stock.inventory.line'].search(domain_stock_inv)
                stock_inv_pool = []

                for line in inv_line:
                    stock_inv_pool += [line.inventory_id]
                    # necesito poder saltarme la compañia
                    line.sudo().write(new_line_vals)

            for stock_inv in stock_inv_pool:
                stock_inv.sudo().action_done()

        return True
