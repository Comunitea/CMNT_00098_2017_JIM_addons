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

class StockInventoryIssue(models.Model):

    _name = "stock.inventory.issue"
    pending_qty = fields.Float("Pending Qty")
    product_id = fields.Many2one('product.product')
    active = fields.Boolean('Pending', default="True")

class StockInventoryLineSGA(models.Model):

    _inherit = "stock.inventory.line"

    from_sga = fields.Boolean("From mecalux", default=False)

    global_qty = fields.Float(
        'Global Quantity', compute='_compute_global_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True)

    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_global_qty(self):

        ctx = dict(self._context)
        ctx.update({'force_company': self.company_id.id, 'location_id': [self.location_id.id]})
        total_qties = self.product_id.sudo()._product_available()
        if total_qties:
            self.global_qty = total_qties[self.product_id.id]['qty_available']

        # if not self.product_id:
        #     self.global_qty = 0
        # else:
        #     global_qty = sum([x.qty for x in self._get_quants_global()])
        #     if global_qty and self.product_uom_id and self.product_id.uom_id != self.product_uom_id:
        #         global_qty = self.product_id.uom_id._compute_quantity(global_qty, self.product_uom_id)
        #     self.global_qty = global_qty

    # def _get_quants_global(self):
    #     return self.env['stock.quant'].search([
    #         ('location_id', '=', self.location_id.id),
    #         ('lot_id', '=', self.prod_lot_id.id),
    #         ('product_id', '=', self.product_id.id),
    #         ('owner_id', '=', self.partner_id.id),
    #         ('package_id', '=', self.package_id.id)])

    def _get_move_values(self, qty, location_id, location_dest_id):

        res = super(StockInventoryLineSGA, self)._get_move_values(qty, location_id, location_dest_id)
        # res['company_id'] = inventory_id.company_id.id >> move company ...
        res['company_id'] = self.company_id.id
        return res
    #
    # @api.onchange('product_id')
    # def onchange_product(self):
    #     if self.product_id and self.from_sga:
    #         self.company_id = self.product_id.company_id
    #     return super(StockInventoryLineSGA, self).onchange_product()

class StockInventorySGA(models.Model):

    _inherit = "stock.inventory"

    @api.multi
    def get_stock_query_from_mecalux(self):

        ids = self.env['sga.file'].process_sga_files(file_type='STO')
        view = self.env.ref('stock'
                            '.view_inventory_tree')
        view_form = self.env.ref('stock'
                                 '.view_inventory_form')

        res = {
            'name': 'Inventories',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': unicode([('id', 'in', ids)]),
            'res_model': 'stock.inventory',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(view.id, 'tree'), (view_form.id, 'form')]
        }
        return res

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
        sga_file_name = sga_file.name
        sga_file = open(sga_file.sga_file, 'r')
        sga_file_lines = sga_file.readlines()

        sga_file.close()
        pool_ids = []
        inventories = []
        warehouse_id = False
        black_company = self.env['res.company'].search([('parent_id','=',False)])[0]
        warehouse_code = "PLS"
        warehouse_id = self.env['stock.warehouse'].search([('code', '=', warehouse_code)])
        location_id = warehouse_id.lot_stock_id
        for line in sga_file_lines:
            if len(line) != 423:
                continue
            # POR RENDIMIENTO LO HAGO AL PRINCIPIO Y GENERICO
            # Warehouse code
            # st = 0
            en = 10
            # warehouse_code = line[st:en].strip()
            # if not warehouse_id:
            #     warehouse_id = self.env['stock.warehouse'].search([('code', '=', warehouse_code)])
            #     # POR SEGURIDAD
            #     if not warehouse_id.sga_integrated:
            #         raise ValidationError("Solo almacenes con gestion SGA")
            #
            #     if not warehouse_id:
            #         raise ValidationError("Codigo de almacen no encontrado")
            #     location_id = warehouse_id.lot_stock_id

            # Product code
            st = en
            en += 50
            product_code = line[st:en].strip()
            # Empty fields
            st = en
            en += 50 + 50 + 14 + 12 + 50 + 14 + 14 + 20 + 50 + 12 + 3 + 50

            # quantity (int + dec >> float)
            st = 399
            st = en
            en += 7
            quantity_int = int(line[st:en])
            st = en
            en += 5
            quantity_dec = float('0.' + line[st:en])
            quantity = quantity_int + quantity_dec

            product_id = self.env['product.product'].search([('default_code', '=', product_code)])
            if not product_id:
                #continue. en producción descomentar esta linea para ignorar stocks no conocidos
                new_prod_vals={'name': u'%s (creado desde inventario %s)'%(product_code, sga_file_name),
                               'default_code': product_code}
                product_id = self.env['product.product'].create(new_prod_vals)

            product_company_id = product_id.company_id
            forced_company_id = black_company

            while quantity > 0.00:
                quantity, new_inventory = self.reg_stock(product_id,
                                                         location_id, product_company_id,
                                                         quantity, forced_company_id=forced_company_id)
                if new_inventory:
                    inventories.append(new_inventory)
                if not forced_company_id and quantity > 0.00:
                    issue_vals = {'pending_qty': quantity,
                            'product_id': product_id.id}
                    self.env['stock.inventory.issue'].create(issue_vals)
                    quantity = 0.00
                forced_company_id = False

            ## TODO DE MOMENTO NO HACEMOS EL action_done, pendiente de confirmar que es automatico
            # for stock_inv in stock_inv_pool:
            #     stock_inv.sudo().action_done()

        return pool_ids




    def new_inv_line(self, product_id, qty, inventory_id):

        # Si hay alguno pendiente lo borro
        domain = [('product_id', '=', product_id.id),
                  ('location_id', '=', inventory_id.location_id.id),
                  ('company_id', '=', inventory_id.company_id.id),
                  ('state', 'in', ('draft', 'confirm'))]
        inventory_line = self.env['stock.inventory.line'].search(domain)

        if inventory_line:
            inventory_line.unlink()
        new_line_vals = {
            'product_id': product_id.id,
            'product_qty': qty,
            'inventory_id': inventory_id.id,
            'company_id': inventory_id.company_id.id,
            'location_id': inventory_id.location_id.id,
            'from_sga': True
        }
        new_inventory_line = self.env['stock.inventory.line'].sudo().create(new_line_vals)
        return new_inventory_line


    def get_inventory_for(self, product_id, location_id, company_id):

        #miro si hay un inventario abierto para esta compañia y si no lo creo
        domain = [('location_id','=', location_id.id),
                  ('company_id','=',company_id.id),
                  ('state', '=', 'confirm')]
        inventory = self.env['stock.inventory'].search(domain)

        if not inventory:
            stock_inv_vals = {
                'name': u'%s (%s)' % ("MECALUX / ", company_id.ref),
                'location_id': location_id.id,
                'filter': 'partial',
                'company_id': company_id.id
            }
            #lo tengo que poner como sudo
            inventory = self.env['stock.inventory'].sudo().create(stock_inv_vals)
        inventory = inventory[0]
        inventory.action_start()
        return inventory




    def reg_stock(self, product_id, location_id, company_id, qty_to_reg, forced_company_id = False):

        if not product_id or not location_id or not company_id:
            return 0.00, False

        ## FUNCION QUE REGULARIZA STOCK

        ## CASO 1 . LO QUE HAY COINCIDE CON ODOO >> NO SE HACE NADA
        ## CASO 2 . HAY MAS EN MECALUX QUE EN ODOO.
                ## SE REGULARIZA EL STOCK EN LA COMPAÑIA DEL PRODUCTO

        ## CASO 3 . HAY MENOS EN MECALUEX QUE EN ODOO.
            ##SE REGULARIZA PRIMERO LA COMPAÑIA forced_company_id. Si no hay, se sale y se vuielve a llamar sin forced_comapny
            ##Para regularizar:
                ## Si el stock de la compañia es mayor que la nueva cantidad entonces ok,
                ## EXCEPTO que la nueva cantidad sea menor que 0, en ese caso se pone 0 y se seteael restante a la parte negativa
                ## No debería pasar que la nueva cantidad sea mayor que la cantidad de la compañia (CASO 2)

        ctx = dict(product_id._context)
        ctx.update({'location_id': [location_id.id], 'from_sga': True})
        total_qties = product_id.with_context(ctx).sudo()._product_available()
        total_qty = total_qties[product_id.id]['qty_available']

        #caso 1. Evidente ...
        if qty_to_reg == total_qty:
            return 0.00, False
        #caso 2. Se regulariza a mayores la compañia del producto
        elif qty_to_reg > total_qty:
            # hay mas stock, entonce se suma a la compañia del producto, se regulariza todo
            ctx = dict(product_id._context)
            ctx.update({'force_company': company_id.id, 'location_id': [location_id.id]})
            total_qties = product_id.with_context(ctx).sudo()._product_available()
            company_qty = total_qties[product_id.id]['qty_available']
            #la nueva cantidad será la diferencia del total + la cantidad de la compañia
            new_qty = (qty_to_reg - total_qty) + company_qty
            inventory_id = self.get_inventory_for(product_id, location_id, company_id)
            new_inv_line = self.new_inv_line(product_id, new_qty, inventory_id)
            return 0.00, inventory_id.id


        #caso 3. Hay menos en Odoo que mecalux


        elif qty_to_reg < total_qty:
            ctx = dict(product_id._context)
            #empezamos con forced_company_id
            company_id = forced_company_id or company_id

            ctx.update({'force_company': company_id.id, 'location_id': [location_id.id]})
            total_qties = product_id.with_context(ctx).sudo()._product_available()
            company_qty = total_qties[product_id.id]['qty_available']
            # la nueva cantidad será la diferencia del total + la cantidad de la compañia
            # new_qty es la nueva cantidad
            new_qty = (qty_to_reg - total_qty) + company_qty

            # si la compañia forzada no tiene stock, devolvemos la misma cantidad, y volvemos sin forced_company
            if company_qty == 0.00 and forced_company_id:
                return qty_to_reg, False
            # Si la cantidad en la compañia es mayor que el nuevo valor > OK
            # excepto si es 0
            elif company_qty >= new_qty:
                #Si new_qty es negativo, lo seteo a 0 y devuelvo la parte negativa
                if new_qty < 0.00:
                    qty_to_reg = - new_qty
                    new_qty = 0.00
                else:
                    qty_to_reg = 0.00

                inventory_id = self.get_inventory_for(product_id, location_id, company_id)
                new_inv_line = self.new_inv_line(product_id, new_qty, inventory_id)
                return qty_to_reg, inventory_id.id

            elif company_qty < new_qty:
                #NO DEBERÍA PASAR ????? Sería caso 1
                inventory_id = self.get_inventory_for(product_id, location_id, company_id)
                new_inv_line = self.new_inv_line(product_id, 0, inventory_id)
                return qty_to_reg - company_qty, inventory_id.id






