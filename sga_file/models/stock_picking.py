# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta
import sga_file
import os
import re


class StockWarehouseSGA(models.Model):

    _inherit = "stock.warehouse"
    sga_integrated = fields.Boolean('Integrado con Mecalux', help="If checked, odoo export this pick type to Mecalux")

class StockPickingTypeSGA(models.Model):

    _inherit = "stock.picking.type"

    sga_integrated = fields.Boolean('Integrado con Mecalux', help="If checked, odoo export this pick type to Mecalux")
    sgavar_file_id = fields.Many2one('sgavar.file', 'SGA Type')

class StockPickingSGAType(models.Model):

    _name = "stock.picking.sgatype"
    _rec_name = "code"

    code = fields.Char("Tipo de venta (SGA)", size=30, default="CORDER")
    description = fields.Char("Descripcion (SGA)", size=100)

class StockPackOperationSGA(models.Model):

    _inherit = "stock.pack.operation"
    _order = "result_package_id desc, line_number asc, id"

    product_code = fields.Char(related="product_id.default_code")
    uom_code = fields.Char(related="product_uom_id.sga_uom_base_code")
    line_number = fields.Integer("Number de linea")
    sga_catch_weight = fields.Selection([('1', 'True'), ('0', 'False')], 'Catch weight',
                                        help="1 Indica si se captura el peso del producto\n"
                                             "0 (por defecto) se coge el peso de la ficha de producto", default='0')
    sga_sustitute_qty = fields.Float("Sustitute qty", help="Si se informa sustitute_prod_code, es la cantidad\n"
                                                           "de producto a sustituir", default=0)

    sga_disable_alt_product = fields.Selection([('1', 'True'), ('0', 'False')], 'Disable alt product',
                                        help="1 Se deshabilita el producto alternativo\n"
                                             "0 (por defecto) No se deshabilita", default='1')


class StockPickingSGA(models.Model):

    _inherit = "stock.picking"

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='A')
    warehouse_id = fields.Many2one(related="picking_type_id.warehouse_id")
    warehouse_code = fields.Char(related="picking_type_id.warehouse_id.code")

    code = fields.Char("Sale order type code", size=30)
    description = fields.Char("Sale order type description", size=100)

    stock_picking_sgatype_id = fields.Many2one('stock.picking.sgatype', string ="Tipo de albaran/venta (SGA)")
    stock_picking_sgatype_code = fields.Char(related="stock_picking_sgatype_id.code")
    stock_picking_sgatype_description = fields.Char(related="stock_picking_sgatype_id.description")

    sga_priority = fields.Integer("Priority", defatult=100)
    account_code = fields.Char(related="partner_id.ref")
    delivery_inst = fields.Char("Avisos para la entrega (SGA)", size=255)
    verify_stock = fields.Selection([('1', 'True'), ('0', 'False')], 'Verifica stock', default='0')
    sga_company = fields.Char(related="partner_id.name")
    sga_state = fields.Char('Estado Mecalux', default="no_sga")

    @api.multi
    def write(self, vals):
        ids_to_meca = []
        for pick in self:

            #TODO Definir en que estado se envia a Mecalux
            #TODO Mirar si es mejor todos juntos o de uno en uno

            if vals.get('state', False) != 'assigned':
                if pick.picking_type_id.sga_integrated:
                    vals['sga_state'] = 'PENDIENTE MECALUX'
                    try:
                        pick.new_mecalux_file()
                    except:
                        vals['sga_state'] = 'ERROR AL ENVIAR A MECALUX'

            return super(StockPickingSGA,self).write(vals)

    def get_outputs_from_mecalux(self):
        file_id = self.env['sga.file'].process_sga_files(file_type='CSO')
        file_id = self.env['sga.file'].process_sga_files(file_type='CRP')

    @api.multi
    def new_mecalux_file(self):

        global_ids = dict()
        for pick in self:
            if pick.picking_type_id.sga_integrated:
                global_ids[pick.picking_type_id.id] = {}
                global_ids[pick.picking_type_id.id]['code'] = pick.picking_type_id.sgavar_file_id.code
                if 'ids' in global_ids[pick.picking_type_id.id]:
                    global_ids[pick.picking_type_id.id]['ids'] += [pick.id]
                else:
                    global_ids[pick.picking_type_id.id]['ids'] = [pick.id]

        if not global_ids:
            raise ValidationError("No hay albaranes para enviar a Mecalux")
        for ids in global_ids:
            picks = global_ids[ids]
            new_sga_file = self.env['sga.file'].check_sga_file('stock.picking', picks['ids'], picks['code'])

        return True

    @api.multi
    def do_transfer(self):
        return super(StockPickingSGA, self).do_transfer()

    @api.multi
    def action_confirm(self):
        res = super(StockPickingSGA, self).action_confirm()
        self.renum_operation_line_number()
        return res

    @api.multi
    def renum_operation_line_number(self):
        for pick in self:
            if pick.picking_type_id.sga_integrated:
                cont = 1
                print "Contador de op: %s" %cont
                for op in pick.pack_operation_product_ids:
                    op.line_number = cont
                    cont += 1

    def return_val_line(self, line, code):
        sgavar = self.env['sgavar.file'].search([('code', '=', 'CSO')])
        if not sgavar:
            raise ValidationError("Modelo no encontrado")
        st = 0
        en = 0
        val = {}
        for var in sgavar.sga_file_var_ids:

            if var.length_dec == 0:
                en = st + var.length
                val[var.name] = line[st:en].strip()
                st = en
            else:
                en = st + var.length_int
                quantity_int = int(line[st:en])
                st = en
                en = st + var.length_dec
                quantity_dec = int(line[st:en]) / 5000
                val[var.name] = quantity_int + quantity_dec
                st = en

        return val

    def import_mecalux_CSO(self, file_id):


        pick_obj = self.env['stock.picking']
        sga_file_obj = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file_obj.sga_file, 'r')
        sga_file_lines = sga_file.readlines()
        sga_file.close()
        str_error = ''
        bool_error = False
        loop = 0
        line_detail = False
        num_details = 0
        n_line = 0
        sgavar = self.env['sgavar.file'].search([('code', '=', 'CSO')])
        pick = False
        if not sgavar:
            raise ValidationError("Modelo no encontrado")

        for line in sga_file_lines:
            n_line += 1
            if line_detail:
                line_detail = False
                continue
            if loop < num_details:
                try:
                    st = 0
                    en = st + 10
                    line_number = int(line[st:en].strip())
                    st = en + 50 + 50
                    en = st + 12
                    served_qty = sga_file_obj.format_from_mecalux_number(line[st:en].strip(), (12, 7, 5))
                    ops[line_number].qty_done = served_qty
                except:
                    str_error += "Error en linea ...%s "% n_line
                    sga_file_obj.write_log(str_error)
                    bool_error = True

                line_detail = True
                loop += 1
                continue
            if pick:
                if bool_error:
                    pick.sga_state = 'ERROR. NO ACTION DONE'
                else:
                    fd = 'HAGO ACTION DONE ' #pick.action_done()

            val = self.return_val_line(line, 'CSO')
            pick = pick_obj.search([('name', '=', val['sorder_code'])])
            if not pick:
                raise ValidationError("Albaran no encontrado: %s" % val['sorder_code'])

            domain = [('picking_id', '=', pick.id)]
            ops = self.env['stock.pack.operation'].search(domain, order="line_number asc")
            if not ops:
                raise ValidationError("Albaran sin operaciones: %s"%pick.id)

            num_details = int(val['line_number_ids'] or 1)
            pick.sga_state = val['sga_state'].strip()
            pick.date_done = sga_file_obj.format_from_mecalux_date(val['date_done'])
            error = ''
            bool_error = False


        return True

    def import_mecalux_CRP(self, file_id):

        pick_obj = self.env['stock.picking']
        sga_file_obj = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file_obj.sga_file, 'r')
        sga_file_lines = sga_file.readlines()
        sga_file.close()
        stock_inv_pool = []
        loop = 0
        line_detail = False
        num_details = 0
        sgavar = self.env['sgavar.file'].search([('code', '=', 'CSO')])

        if not sgavar:
            raise ValidationError("Modelo no encontrado")

        for line in sga_file_lines:

            if line_detail:
                line_detail = False
                continue

            if loop < num_details:
                loop += 1
                st = 188
                en = st + 10
                line_number = int(line[st:en].strip()) - 1

                st = 186
                en = st + 12
                served_qty = sga_file_obj.format_from_mecalux_number(line[st:en].strip(), (12, 7, 5))

                ops[line_number].qty_done = served_qty
                line_detail = True
                continue

            val = self.return_val_line(line, 'CSO')
            pick = pick_obj.search([('name', '=', val['rec_order_code'])])
            if not pick:
                raise ValidationError("Albaran no encontrado: %s" % val['rec_order_code'])

            domain = [('picking_id', '=', pick.id)]
            ops = self.env['stock.pack.operation'].search(domain, order="line_number asc")
            if not ops:
                raise ValidationError("Albaran sin operaciones %s"%pick.id)

            num_details = int(val['line_number_ids'] or 1)
            pick.sga_state = val['sga_state'].strip()

            pick.date_done = sga_file_obj.format_from_mecalux_date(val['date_done'])

        return True