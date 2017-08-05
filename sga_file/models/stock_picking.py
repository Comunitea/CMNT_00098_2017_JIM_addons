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
    sga_integrated = fields.Boolean('Integrado con Mecalux',
                                    help="If checked, odoo export this pick type to Mecalux")

class StockPickingTypeSGA(models.Model):

    _inherit = "stock.picking.type"

    sga_integrated = fields.Boolean('Integrado con Mecalux',
                                    help="If checked, odoo export this pick type to Mecalux")
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

    container_id = fields.Many2one('sga.container')
    container_src_id = fields.Many2one('sga.container')
    sga_changed = fields.Boolean ('SGA modified/created', default=False)


class StockPickingSGA(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def _get_account_code(self):
        for pick in self:
            res = pick.partner_id.ref
            partner = pick.partner_id
            while partner.parent_id:
                partner = partner.parent_id
                if partner:
                    res = partner.ref
            pick.account_code = res
        return res

    @api.multi
    def _get_action_done_bool(self):

        action_done =  eval(self.env['ir.config_parameter'].get_param('picking_auto'))
        for pick in self:
            pick.action_done_bool = action_done

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='A')
    warehouse_id = fields.Many2one(related="picking_type_id.warehouse_id")
    warehouse_code = fields.Char(related="picking_type_id.warehouse_id.code")

    code = fields.Char("Sale order type code", size=30)
    description = fields.Char("Sale order type description", size=100)

    stock_picking_sgatype_id = fields.Many2one('stock.picking.sgatype', string ="Tipo de albaran/venta (SGA)")
    stock_picking_sgatype_code = fields.Char(related="stock_picking_sgatype_id.code")
    stock_picking_sgatype_description = fields.Char(related="stock_picking_sgatype_id.description")

    sga_priority = fields.Integer("Priority", default=100)

    delivery_inst = fields.Char("Avisos para la entrega (SGA)", size=255)
    verify_stock = fields.Selection([('1', 'True'), ('0', 'False')], 'Verifica stock', default='0')
    sga_company = fields.Char(related="partner_id.name")
    sga_state = fields.Selection ([('NI', 'Sin integracion'),
                                   ('NE', 'No exportado'),
                                   ('PM', 'Pendiente Mecalux'),
                                   ('EE', 'Error en exportacion'),
                                   ('EI', 'Error en importacion'),
                                   ('MT', 'Realizado'),
                                   ('MC', 'Cancelado')], 'Estado Mecalux', default="NI", track_visibility='onchange')

    shipping_city = fields.Char(related="partner_id.state_id.name")
    shipping_partner_name = fields.Char(related="partner_id.name")
    account_code = fields.Char("Account code", compute="_get_account_code")

    action_done_bool = fields.Boolean("Validación automática", default=_get_action_done_bool)
    sga_integrated = fields.Boolean(related="picking_type_id.sga_integrated")

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        if self.picking_type_id.sga_integrated:
            self.sga_state = 'NE'
        else:
            self.sga_state = 'NI'
        return super(StockPickingSGA, self).onchange_picking_type()

    @api.model
    def create(self, vals):
        if vals['picking_type_id']:
            picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
            if picking_type:
                if picking_type.sga_integrated:
                    vals['sga_state'] = "NE"
        pick = super(StockPickingSGA, self).create(vals)
        return pick

    @api.multi
    def write(self, vals):
        return super(StockPickingSGA, self).write(vals)

    def get_outputs_from_mecalux(self):
        self.env['sga.file'].process_sga_files(file_type='ZCS')
        self.env['sga.file'].process_sga_files(file_type='CRP')

    @api.multi
    def move_to_done(self):
        picks = self.filtered(lambda x: x.sga_state != 'NI')
        picks.write({'sga_state': 'MT'})

    @api.multi
    def move_to_NE(self):
        sga_states_to_NE = ('PM', 'EI', 'EE', 'MT', False)
        picks = self.filtered(lambda x: x.sga_state in sga_states_to_NE)
        picks.write({'sga_state': 'NE'})

    @api.multi
    def new_mecalux_file(self, operation=False):
        ctx = dict(self.env.context)
        if operation:
            ctx['operation'] = operation
        if 'operation' not in ctx:
            ctx['operation'] = 'A'

        picks=[]
        for pick in self:

            if pick.sga_state != 'NE':
                raise UserError("Solo puedes enviar en estado 'No enviado'")

            new_sga_file = self.env['sga.file'].with_context(ctx).\
                check_sga_file('stock.picking', pick.id, pick.picking_type_id.sgavar_file_id.code)
            if new_sga_file:
                picks.append(pick.id)

        if picks:
            self.env['stock.picking'].browse(picks).write({'sga_state': 'PM'})
        else:
            raise ValidationError("No hay albaranes para enviar a Mecalux")
        return True

    @api.multi
    def renum_operation_line_number(self):
        for pick in self:
            if pick.picking_type_id.sga_integrated:
                cont = 1
                for op in pick.pack_operation_product_ids:
                    op.line_number = cont
                    cont += 1

    def return_val_line(self, line, code):

        sgavar = self.env['sgavar.file'].search([('code', '=', code)])
        if not sgavar:
            raise ValidationError("Modelo no encontrado")
        st = 0
        en = 0
        val = {}

        for var in sgavar.sga_file_var_ids:
            if var.length_dec == 0:
                en = st + var.length
                val[var.name] = line[st:en].strip() or var.fillchar
                st = en
            else:
                en = st + var.length_int
                quantity_int = int(line[st:en].strip() or 0)
                st = en
                en = st + var.length_dec
                quantity_dec = int(line[st:en].strip() or 0) / 5000
                val[var.name] = quantity_int + quantity_dec
                st = en
        return val

    def import_mecalux_CSO(self, file_id):
        return False

    def import_mecalux_CRP(self, file_id):

        pick_obj = self.env['stock.picking']
        sga_file_obj = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file_obj.sga_file, 'r')
        sga_file_lines = sga_file.readlines()
        sga_file.close()
        bool_error = False
        LEN_HEADER = 460
        LEN_LINE = 362
        LEN_DETAIL_LINE = 88
        pool_ids = []
        n_line=0
        create = False
        pick = False
        for line in sga_file_lines:
            line = line.strip()
            n_line += 1
            if len(line) == LEN_HEADER:

                if pick:
                    if pick.action_done_bool:
                        pick.action_done()
                    pick = False
                #Busco pick

                st = 40
                en = st + 30
                rec_order_code = line[st:en].strip()
                pick = pick_obj.search([('name', '=', rec_order_code)])
                #if not pick:
                #    pick = pick_obj.search([('backorder_id.name', '=', rec_order_code), ('sga_state', 'in', ('PM', 'EI'))])
                if pick:
                    pool_ids.append(pick.id)
                    st = 70
                    en = st+30
                    sga_state = line[st:en].strip()
                    pick.sga_state = "MT" if sga_state == "CLOSE" else "MC"

                    date_done
                    st = 100
                    en = st + 14
                    date_done = line[st:en].strip()
                    pick.date_done = sga_file_obj.format_from_mecalux_date(date_done)

                    st = 378
                    en = st + 10
                    weight = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))
                    pick.pick_weight = weight

                    st = 388
                    en = st + 10
                    bultos = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))
                    pick.number_of_packages = bultos

                    st = 398
                    en = st + 50
                    carrier_code = line[st:en].strip()
                    domain = [('carrier_code', '=', carrier_code)]
                    carrier = self.env['delivery.carrier'].search(domain)
                    pick.carrier_id = carrier

                    domain = [('picking_id', '=', pick.id)]
                    ops = self.env['stock.pack.operation'].search(domain, order="line_number asc")

                else:
                    str_error = "Codigo de albaran %s no encontrado o estado incorrecto en linea ...%s " % (rec_order_code, n_line)
                    sga_file_obj.write_log(str_error)

            elif len(line) == LEN_LINE and pick:
                # cantidad a realizada
                st = 186
                en = st + 12
                qty_done = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (12, 7, 5))

                st = 210
                en = st + 10
                op_id = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))
                op = self.env['stock.pack.operation'].search([('id', '=', op_id)])

                # Si op existe, escribo qty_done, si no creo una linea de operacion con lo recibido
                if op:
                    op.qty_done += qty_done
                    op.sga_changed = True

                elif create:
                    st = 62
                    en = st + 10
                    uom_code = line[st:en].strip()
                    uom = self.env['product.uom'].search([('sga_uom_base_code', '=', uom_code)])
                    if not uom:
                        uom = self.env['product.uom'].create({'name': uom_code,
                                                              'sga_uom_base_code': uom_code,
                                                              'category_id': 1})
                        str_error = "Unidad %s creada en linea ...%s " % (uom_code, n_line)
                        sga_file_obj.write_log(str_error)
                    # Producto asociado al codigo product_code
                    st = 0
                    en = st + 50
                    product_code = line[st:en].strip()
                    product = self.env['product.product'].search([('default_code', '=', product_code)])
                    if not product:
                        product = self.env['product.product'].create({'name': product_code,
                                                                      'default_code': product_code,
                                                                      'uom_id': uom.id})
                    str_error = "Producto %s creado en linea ...%s " % (product_code, n_line)
                    sga_file_obj.write_log(str_error)
                    values = {'picking_id': pick.id,
                              'product_id': product.id,
                              'sga_changed': True,
                              'qty_done': qty_done,
                              'product_uom_id': uom.id,
                              'location_id': pick.location_id.id or pick.picking_type_id.default_location_src_id.id,
                              'location_dest_id': pick.location_dest_id.id or pick.picking_type_id.default_location_dest_id.id}
                    new_op = self.env['stock.pack.operation'].create(values)
                    if new_op:
                        str_error = "Operacion [%s] creada para %s [%s %s]en linea ...%s " \
                                %(new_op.id, product.name, qty_done, uom_code, n_line)
                        sga_file_obj.write_log(str_error)


                    else:
                        str_error = "Error al crear operacion para para %s [%s %s]en linea ...%s " \
                                    % (new_op.id, product.name, qty_done, uom_code, n_line)
                        sga_file_obj.write_log(str_error)
            else:
                continue
        ops_product = pick.pack_operation_product_ids.filtered(lambda x: x.product_id.type == 'product')
        for op in ops_product:
            op.qty_done = op.product_qty

        if not bool_error and pick:
            if pick.action_done_bool:
                pick.action_done()

        return list(set(pool_ids))

    def import_mecalux_ZCS(self, file_id):

        pick_obj = self.env['stock.picking']
        sga_file_obj = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file_obj.sga_file, 'r')
        sga_file_lines = sga_file.readlines()
        sga_file.close()
        str_error = ''
        bool_error = False
        pool_ids = []
        n_line = 0
        sgavar = self.env['sgavar.file'].search([('code', '=', 'CSO')])
        pick = False
        if not sgavar:
            raise ValidationError("Modelo no encontrado")
        create=False
        LEN_HEADER = 468 + 2
        LEN_LINE = 342 + 2
        LEN_DETAIL_LINE = 434 + 2
        for line in sga_file_lines:
            n_line += 1
            if len(line) == LEN_HEADER:
                if pick:
                    if pick.action_done_bool:
                        pick.action_done()
                    pick = False

                #Buscamos el pick asociado. (sorder_code)
                st = 10
                en = st + 50
                sorder_code = line[st:en].strip()

                pick = pick_obj.search([('name', '=', sorder_code), ('sga_state', 'in', ('PM','EI'))])
                if not pick:
                    str_error += "Codigo de albaran %s no encontrado o estado incorrecto en linea ...%s " % (sorder_code, n_line)
                    sga_file_obj.write_log(str_error)
                    bool_error = True
                    return False
                else:
                    pool_ids.append(pick.id)

                st = 378
                en = st + 10
                weight = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))
                pick.pick_weight = weight

                st = 388
                en = st + 10
                bultos = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))
                pick.number_of_packages = bultos

                st = 398
                en = st + 50
                carrier_code = line[st:en].strip()
                domain = [('carrier_code', '=', carrier_code)]
                carrier = self.env['delivery.carrier'].search(domain)
                pick.carrier_id = carrier

                # Date_done de la fecha
                st = 90
                en = st+14
                date_done = sga_file_obj.format_from_mecalux_date(line[st:en].strip())
                self.date_done

            elif len(line) == LEN_LINE and pick:
                #Buscamos la operacion relacionada
                st = 0
                en = st + 10
                op_id = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))
                op = self.env['stock.pack.operation'].search([('id', '=', op_id), ('picking_id', '=', pick.id)])

                # cantidad a realizar
                st = 284
                en = st + 122
                qty_done = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (12, 7, 5))

                # Si op existe, escribo qty_done, si no creo una linea de operacion con lo recibido
                if op:# and op.product_id.id == product.id:
                    op.qty_done += qty_done
                    op.sga_changed = True

                elif create:
                    st = 186
                    en = st + 10
                    uom_code = line[st:en].strip()
                    uom = self.env['product.uom'].search([('sga_uom_base_code', '=', uom_code)])
                    if not uom:
                        uom = self.env['product.uom'].create({'name': uom_code,
                                                              'sga_uom_base_code': uom_code,
                                                              'category_id': 1})
                    # Producto asociado al codigo product_code
                    st = 10
                    en = st + 50
                    product_code = line[st:en].strip()
                    product = self.env['product.product'].search([('default_code', '=', product_code)])
                    if not product:
                        product = self.env['product.product'].create({'name': product_code,
                                                                      'default_code': product_code,
                                                                      'uom_id': uom.id})
                    values = {'picking_id': pick.id,
                            'product_id': product.id,
                            'sga_changed': True,
                            'qty_done': qty_done,
                            'product_qty': qty_done,
                            'product_uom_id': uom.id,
                            'location_id': pick.location_id.id or pick.picking_type_id.default_location_src_id.id,
                            'location_dest_id': pick.location_dest_id.id or pick.picking_type_id.default_location_dest_id.id}
                    # NO CREO OPERACIONES NUEVAS PARA SALIDAS SIN OPS
                    self.env['stock.pack.operation'].create(values)

            else:
                len(line) == LEN_DETAIL_LINE
                continue
            #supongo que las cantidades de type!=product hay siempre
            ops_product = pick.pack_operation_product_ids.filtered(lambda x:x.product_id.type == 'product')
            for op in ops_product:
                op.qty_done = op.product_qty

            if bool_error:
                pick.sga_state = 'EI'
            elif pick.action_done_bool:
                pick.action_done()

        return list(set(pool_ids))