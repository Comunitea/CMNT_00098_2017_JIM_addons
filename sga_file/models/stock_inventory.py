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
    pending_qty = fields.Float("Cantidad pendiente")
    product_id = fields.Many2one('product.product')
    active = fields.Boolean('ACK', default="True")
    notes = fields.Char('Notas')


class ProductProduct(models.Model):
    _inherit = "product.product"

    def compute_global_qty(self, location_id=False, force_company=False):
        domain = ([('product_id', '=', self.id), ('location_id', '=', location_id)])
        if force_company:
            domain += [('company_id', '=', force_company)]
        quants_res = dict((item['product_id'][0], item['qty']) for item in
                          self.env['stock.quant'].sudo().read_group(domain, ['product_id', 'qty'], ['product_id']))
        global_qty = quants_res.get(self.id, 0.0)
        return global_qty

class StockInventoryLineSGA(models.Model):

    _inherit = "stock.inventory.line"

    from_sga = fields.Boolean("From mecalux", default=False)
    stock_mecalux = fields.Float('Global stock (Mecalux)', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    global_qty = fields.Float(
        'Global stock (Odoo)', compute='_compute_global_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True)


    @api.depends('location_id', 'product_id')
    def _compute_global_qty(self):
        for line in self:
            line.global_qty = line.product_id.compute_global_qty(location_id=line.location_id.id)

    def _get_move_values(self, qty, location_id, location_dest_id):
        res = super(StockInventoryLineSGA, self)._get_move_values(qty, location_id, location_dest_id)
        res['company_id'] = self.company_id.id
        return res

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
        inventories = []
        warehouse_id = False

        line_number = 0
        for line in sga_file_lines:

            if len(line) != 423:
                continue
            # POR RENDIMIENTO LO HAGO AL PRINCIPIO Y GENERICO
            # Warehouse code
            st = 0
            en = 10
            if not warehouse_id:
                warehouse_code = line[st:en].strip()
                warehouse_id = self.env['stock.warehouse'].search([('code', '=', warehouse_code)])
                location_id = warehouse_id.lot_stock_id
                # POR SEGURIDAD
                if not warehouse_id.sga_integrated:
                    raise ValidationError("Solo almacenes con gestion SGA")


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
            line_number+=1
            if not product_id:
                issue_vals = {'notes': 'No existe el código: %s'%product_code,
                              }
                self.env['stock.inventory.issue'].create(issue_vals)
                print "%s: %s No está en ODOO"%(product_code, quantity)
                continue
            if len(product_id)>1:
                issue_vals = {'notes': 'Código duplicado: %s'%product_code,
                              }
                self.env['stock.inventory.issue'].create(issue_vals)
                print "%s: %s Codigo duplicado en ODOO"%(product_code, quantity)
                continue

            #print "%s %s: %s" % (line_number, product_code, quantity)
            product_company_id = product_id.company_id

            first = True
            reg_qty = 0.00
            reg_qty_done = 0.00
            original_qty = quantity
            while quantity > 0.00:
                quantity, new_inventory, reg_qty = self.reg_stock(product_id,
                                                         location_id, product_company_id,
                                                         quantity, reg_qty, force_company=first)
                reg_qty_done += reg_qty
                if new_inventory:
                    inventories.append(new_inventory)

                if not first and quantity > 0.00:
                    issue_vals = {
                          'pending_qty': original_qty - reg_qty_done,
                          'product_id': product_id.id,
                          'notes': 'Incidencia',}
                    self.env['stock.inventory.issue'].create(issue_vals)
                    quantity = 0.00
                first = False

            ## TODO DE MOMENTO NO HACEMOS EL action_done, pendiente de confirmar que es automatico
            action_done = True if self.env['ir.config_parameter'].get_param('inventary_auto') == u'True' else False
            if action_done:
                for stock_inv in inventories:
                    stock_inv.sudo().action_done()
        return inventories

    def new_inv_line(self, product_id, qty, inventory_id, mecalux_stock=0.00):

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
            'stock_mecalux': mecalux_stock,
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




    def reg_stock(self, product_id, location_id, company_id, qty_to_reg, reg_qty, force_company = False):

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

        odoo_qty = product_id.compute_global_qty(location_id=location_id.id)
        mecalux_qty = qty_to_reg
        #caso 1. Evidente ...
        if mecalux_qty == odoo_qty:
            return 0.00, False, 0.00

        #caso 2. Menos en Odoo: Se regulariza a mayores la compañia del producto
        elif mecalux_qty > odoo_qty:
            company_id = product_id.company_id
            inventory_id = self.get_inventory_for(product_id, location_id, company_id)
            new_inv_line = self.new_inv_line(product_id, 0.0, inventory_id, mecalux_qty)
            new_inv_line.product_qty = new_inv_line.theoretical_qty + (qty_to_reg - odoo_qty)
            return 0.00, inventory_id.id, 0.00

        #caso 3. Hay mas en Odoo que mecalux
        elif mecalux_qty < odoo_qty:
            qty_to_reg = (odoo_qty - mecalux_qty - reg_qty)
            if force_company:
                #Busco stock en Pallatium, si hay fuerzo la compañia
                force_company = self.env['res.company'].search([('ref', '=', 'PALLAT')])
                force_company_qty = product_id.compute_global_qty(location_id=location_id.id,
                                                                  force_company=force_company.id)

                if force_company_qty > 0.00:
                    company_id = force_company

            inventory_id = self.get_inventory_for(product_id, location_id, company_id)
            new_inv_line = self.new_inv_line(product_id, 0.0, inventory_id, mecalux_qty)
            #si la cantidad en la compañia es mayor que lo que necesito ...
            if new_inv_line.theoretical_qty >= qty_to_reg:
                new_inv_line.product_qty = new_inv_line.theoretical_qty - qty_to_reg
                return 0.00, inventory_id.id, 0.00
            else:
                new_inv_line.product_qty = 0
                qty_to_reg = mecalux_qty - new_inv_line.theoretical_qty
                return mecalux_qty, inventory_id.id, new_inv_line.theoretical_qty


    def global_stock_mecalux(self):
        if self.location_id.barcode != 'PLS':
            raise ValidationError ("Solo para almacén de Palas")

        if not self.line_ids:
            self.env['sga.file'].create_global_PST()
        else:
            raise ValidationError("Si quieres selccionar productos, debes hacerlo desde la vista tree de productos")






