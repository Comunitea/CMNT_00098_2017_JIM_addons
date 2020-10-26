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
import logging
_logger = logging.getLogger(__name__)

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
    def compute_sga_shipping_info(self):

        for pick in self:
            sale_id = pick.sudo().orig_sale_id
            if sale_id:
                partner = sale_id.partner_shipping_id
                account_code = sale_id.partner_id.ref
            else:
                partner = pick.partner_id or self.env.user.company_id.partner_id or False
                if partner:
                    account_code = partner.ref
            if partner:
                pick.shipping_city = partner.state_id and partner.state_id.name or partner.country_id and partner.country_id.name or 'Sin definir'
                pick.shipping_partner_name = partner.name or "Sin nombre"
                pick.account_code = account_code

    def _get_action_done_bool(self):
        return True if self.env['ir.config_parameter'].get_param('picking_auto') == u'True' else False

    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='A', copy=False)
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
                                   ('MC', 'Cancelado')], 'Estado Mecalux', default="NI", track_visibility='onchange', copy=False)

    shipping_city = fields.Char(compute=compute_sga_shipping_info, string ="Provincia de entrega")
    shipping_partner_name = fields.Char(compute=compute_sga_shipping_info, string="Nombre cliente")
    account_code = fields.Char(compute=compute_sga_shipping_info, string="Codigo cliente")
    action_done_bool = fields.Boolean("Validación automática", default=_get_action_done_bool)
    do_backorder = fields.Selection([('default', 'Por defecto'), ('yes', 'Si'), ('no', 'No')], "Crea entrega parcial", default='default')
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
                else:
                    vals['sga_state'] = "NI"
        pick = super(StockPickingSGA, self).create(vals)
        return pick

    def check_write_in_pm(self, vals):

        fields_to_check = ('launch_pack_operations', 'pack_operation_product_ids', 'move_lines',
                           'recompute_pack_op')

        fields_list = sorted(list(set(vals).intersection(set(fields_to_check))))
        if len(self.filtered(lambda x: x.sga_state == 'PM')) and fields_list:
            return True
        return False

    @api.multi
    def write(self, vals):
        if 'action_done_bool' in vals:
            for pick in self:
                pick.message_post(
                body="El albarán <em>%s</em> <b>ha cambiado el estado de validación automática a</b> <em>%s</em>" % (pick.name, vals['action_done_bool']))
        if self.check_write_in_pm(vals):
            raise ValidationError("No puedes modificar operaciones si está enviado a Mecalux")

        return super(StockPickingSGA, self).write(vals)

    def get_outputs_from_mecalux(self):
        self.env['sga.file'].process_sga_files(file_type='ZCS')
        self.env['sga.file'].process_sga_files(file_type='CRP')


    def button_move_to_done(self):
        return self.move_to_done

    @api.multi
    def move_to_done(self):
        picks = self.filtered(lambda x: x.sga_state != 'NI')
        picks.write({'sga_state': 'MT'})


    def button_move_to_NE(self):
        return self.move_to_NE

    @api.multi
    def move_to_NE(self):
        sga_states_to_NE = ('PM', 'EI', 'EE', 'MT', 'MC', False)
        picks = self.filtered(lambda x: x.sga_integrated and x.sga_state in sga_states_to_NE)
        picks.write({'sga_state': 'NE'})

    def button_new_mecalux_file(self, ctx):

        return self.with_context(ctx).new_mecalux_file()

    def new_mecalux_file(self, operation=False, force=False):

        ctx = dict(self.env.context)
        if operation:
            ctx['operation'] = operation
        if 'operation' not in ctx:
            ctx['operation'] = 'A'
        self = self.filtered(lambda x: x.sga_state == 'NE')
        states_to_check = ('confirmed', 'partially_available')
        states_to_send = 'assigned'
        picks = []
        pick_to_check = self.filtered(lambda x: x.state in states_to_check and not force)
        if pick_to_check and pick_to_check[0]:
            view = self.env.ref('sga_file.stock_mecalux_confirm_wizard')
            wiz = self.env['stock.mecalux.confirm'].create({'pick_id': pick_to_check.id})
            return {
                'name': 'Confirmación de envio a Mecalux',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.mecalux.confirm',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_id': wiz.id,
                'target': 'new',
                'context': self.env.context,
            }

        for pick in self.filtered(lambda x: x.state in states_to_send or force):
            if not pick.partner_id:
                raise UserError("No puedes enviar un albarán sin asociarlo a una empresa")

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

    def do_pick(self, sga_ops_exists, bool_error=True):
        if not self.picking_type_id.sga_integrated:
            raise ValidationError("Solo albaranes integrados con Mecalux")
        _logger.info("Entro en do_pick para el albarán %s\n Con valores: sga_ops_exists = %s"%(self.name, sga_ops_exists))


        partial = ''
        sga_state = 'MT'
        action_done_bool = self.action_done_bool
        create_partial = False
        ctx = self._context.copy()
        if self.pack_operation_product_ids.filtered(lambda x: x.qty_done != 0):
            all_zero = False
        else:
            all_zero = True

        if not sga_ops_exists:
            _logger.info("No hay operaciones para el albarán %s" % self.name)
            self.message_post(body="Pick <em>%s</em> ha sido realizado en Mecalux pero los <b>ids no se encuentran en ODOO</b>." % (self.name))
            action_done_bool = False
            sga_state = 'EI'

        # Confimo cantidaddes en servicios y consumibles
        pick_ops_product = self.pack_operation_product_ids.filtered(lambda x: x.product_id.type == 'consu')
        _logger.info("Servicios y consumibles: {}".format(pick_ops_product))
        for op in pick_ops_product:
            op.qty_done = op.product_qty
        _logger.info("action_done_bool: {}".format(action_done_bool))
        if action_done_bool:
            all_done = True
            do_transfer = True
            op_not_done = self.pack_operation_product_ids.filtered(lambda x: x.qty_done != x.product_qty)
            _logger.info("op_not_done: {}".format(op_not_done))
            if op_not_done:
                all_done = False
                display_name_ids = ['%s (Cant: %s)' % (x.product_id.display_name, (x.product_qty - x.qty_done)) for x in
                                    op_not_done]
            if all_done:
                _logger.info("all_done: {}".format(all_done))
                _logger.info("Action done")
                self.action_done()
                _logger.info("Albarán %s validado 100%" % self.name)
                self.message_post(body="El albarán <em>%s</em> <b>ha sido validado por Mecalux</b>. Todas las operaciones OK" % (self.name))
                sga_state = 'MT'

            else:
                _logger.info("all_done: {} con do_backorder {} y do_transfer".format(all_done, self.do_backorder, do_transfer))
                if self.do_backorder == 'default':
                    do_transfer = False
                elif self.do_backorder == 'yes':
                    create_partial = True
                elif self.do_backorder == 'no':
                    create_partial = False

                #print "NO TODAS las cantidades OK con do_backorder = %s y do_transfer a %s" % (self.do_backorder, do_transfer)
                if do_transfer:
                    if all_zero:
                        _logger.info("Albarán sin nada hecho %s No se valida" % self.name)
                        # no hay nada hecho >> Solo le cambio el nombre y lo muevo a no enviado
                        # Necesito cambiarle el nombre por Mecalux
                        old_name = self.name
                        new_name = self.env['stock.picking.type'].browse(self.picking_type_id.id).sequence_id.next_by_id()
                        self.do_unreserve()
                        sga_state = 'NE'
                        self.write({'name': new_name, 'sga_state': sga_state})
                        self.message_post(
                                    body=("La orden <em>%s</em> la orden ha sido cerrada en Mecalux sin realizar nada</br>Nuevo nombre en Odoo<b>%s</b>") % (old_name, new_name))
                        return bool_error
                    else:
                        _logger.info("Valido con do_new_transfer")
                        res = self.with_context(ctx).do_new_transfer()
                        wiz_id = res.get('res_id', False)
                        wiz = self.env['stock.backorder.confirmation'].browse(wiz_id)
                        _logger.info("Valido con do_new_transfer {}".format(wiz.display_name))
                        sga_state = 'MT'
                        #print "Creo y encuentro asistente %s"%wiz.id
                        if wiz:
                            if create_partial:
                                wiz.process()
                                partial = "(con parcial) Pendiente:</hr>"
                            else:
                                wiz.process_cancel_backorder()
                                partial = "(sin parcial) No entregado:</hr>"
                        _logger.info("Albarán %s validado %s" % (self.name, partial))
                        self.message_post(body="Pick <em>%s</em> <b>ha sido validado en Mecalux </b> %s %s" % (self.name, partial, display_name_ids))
        self.sga_state = sga_state

        _logger.info("Propago los valores de Mecalux a los elabaranes enlazados ")
        self.propagate_pick_values()
        #print trasnapaso pesos/carrier....
        _logger.info(">>>Ok para %s" % self.name)
        return bool_error

    def import_mecalux_CSO(self, file_id):
        return False

    def import_mecalux_CRP(self, file_id):

        pick_obj = self.env['stock.picking']
        sga_file_obj = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file_obj.sga_file, 'r')
        _logger.info("Importando archivo: %s"%sga_file_obj.sga_file)
        sga_file_lines = sga_file.readlines()
        sga_file.close()
        bool_error = True
        LEN_HEADER = 460
        LEN_LINE = 362
        LEN_DETAIL_LINE = 88
        pool_ids = []
        n_line = 0
        res = False
        create = False
        pick = self.env['stock.picking']
        sga_ops_exists = False
        for line in sga_file_lines:
            line = line.strip()
            n_line += 1
            if len(line) == LEN_HEADER:
                if pick:
                    bool_error = pick.do_pick(sga_ops_exists, bool_error)
                sga_ops_exists = False
                pick = False
                #Busco pick
                st = 40
                en = st + 30
                rec_order_code = line[st:en].strip()
                pick = pick_obj.search([('name', '=', rec_order_code), ('sga_state', 'in', ('MC', 'PM'))])

                #if not pick:
                #    pick = pick_obj.search([('backorder_id.name', '=', rec_order_code), ('sga_state', 'in', ('PM', 'EI'))])
                if pick:
                    _logger.info(">> Albarán: %s"%pick.name)
                    pool_ids.append(pick.id)
                    st = 70
                    en = st+30
                    sga_state = line[st:en].strip()
                    pick.sga_state = "MT" if sga_state == "CLOSE" else "MC"

                    st = 100
                    en = st + 14
                    date_done = line[st:en].strip()
                    pick.date_done = sga_file_obj.format_from_mecalux_date(date_done)
                    if sga_state == 'CANCEL':
                        _logger.info(">> Albarán: %s CANCELADO EN MECALUX" % pick.name)
                        pick.sga_state = "MC"
                        pick.message_post(body="Pick <em>%s</em> <b>ha sido cancelado en Mecalux</b>." % (pick.name))
                        pick = False
                        continue

                    pick.sga_state = "MT"
                else:
                    bool_error = False
                    str_error = "Codigo de albaran %s no encontrado o estado incorrecto en linea ...%s " % (rec_order_code, n_line)


                    error_message = u'Albarán %s no encontrado o en estado incorrecto.' % (rec_order_code)
                    self.create_sga_file_error(sga_file_obj, n_line, 'CRP', pick, 'Pick no válido', error_message)

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

                if op_id and not op:
                    bool_error = False
                    error_message = u'Op %s no encontrada en el albarán %s'%(op_id, pick.name)
                    self.create_sga_file_error(sga_file_obj, n_line, 'CRP', pick, 'Op no encontrada', error_message)

                # Si op existe, escribo qty_done, si no creo una linea de operacion con lo recibido
                if op:
                    _logger.info(">> Línea % s del albarán: %s. Producto: %s Cantidad hecha %s" % (op.id, pick.name, op.product_id.default_code, qty_done))
                    op.qty_done = qty_done
                    op.sga_changed = True
                    sga_ops_exists = True

            else:
                continue
        if pick:
            bool_error = pick.do_pick(sga_ops_exists, bool_error)

        return pool_ids

    def import_mecalux_ZCS(self, file_id):

        res = False
        pick_obj = self.env['stock.picking']
        sga_file_obj = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file_obj.sga_file, 'r')
        _logger.info("Importando archivo: %s" % sga_file_obj.sga_file)
        sga_file_lines = sga_file.readlines()
        sga_file.close()
        str_error = ''
        n_line = 0
        sgavar = self.env['sgavar.file'].search([('code', '=', 'CSO')])
        pick = False
        if not sgavar:
            raise ValidationError("Modelo no encontrado")
        create = False
        LEN_HEADER = 470
        LEN_LINE = 344
        LEN_DETAIL_LINE = 436
        sga_ops_exists = False
        do_pick = False
        pool_ids = []
        for line in sga_file_lines:
            n_line += 1

            if len(line) == LEN_HEADER:
                if pick:
                    pick.do_pick(sga_ops_exists)
                sga_ops_exists = False
                st = 10
                en = st + 50
                sorder_code = line[st:en].strip()
                pick = pick_obj.search([('name', '=', sorder_code)])

                if not pick:

                    str_error += "Codigo de albaran %s no encontrado o estado incorrecto en linea ...%s " % (sorder_code, n_line)
                    error_message =  u'Albarán %s no encontrado o en estado incorrecto.' % (
                                      sorder_code)
                    _logger.info(error_message)
                    self.create_sga_file_error(sga_file_obj, n_line, 'ZCS', pick, 'Pick no válido', error_message)

                    sga_file_obj.write_log(str_error)
                    continue
                _logger.info(">> Albarán: %s" % pick.name)
                pool_ids.append(pick.id)
                st = 60
                en = st + 10
                pick_status = line[st:en].strip()
                if pick_status == "CANCELED":
                    pick.sga_state = 'NE'
                    pick.message_post(body="Pick <em>%s</em> <b>ha sido cancelado en Mecalux</b>." % (pick.name))
                    _logger.info(">> Albarán: %s CANCELADO EN MECALUX" % pick.name)
                    pick = False
                    continue
                if pick.sga_state != "PM":
                    pick.message_post(body="Pick <em>%s</em> <b>ha sido realizado en Odoo antes que en Mecalux</b>." % (pick.name))
                    error_message = u'Albarán %s en estado incorrecto (%s)' % (
                                      sorder_code, pick.state)
                    self.create_sga_file_error(sga_file_obj, n_line,'ZCS',pick,'Pick no válido', error_message)

                    pick = False
                    continue
                #print "###############\nde mecalux %s\n##############"%pick.name

                st = 378
                en = st + 10
                pick_weight = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))

                st = 388
                en = st + 10
                pick_packages = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))

                st = 398
                en = st + 50
                carrier_operario = line[st:en].strip()

                if ',' in carrier_operario:
                    carrier_code, oper_code = carrier_operario.split(',')
                elif '.' in carrier_operario:
                    carrier_code, oper_code = carrier_operario.split('.')
                else:
                    carrier_code = carrier_operario
                    oper_code = False

                domain = [('carrier_code', '=', carrier_code)]
                carrier = self.env['delivery.carrier'].search(domain)

                carrier_id = carrier.id if carrier else False

                if oper_code:
                    domain = [('ref', '=', oper_code)]
                    user_id = self.env['res.users'].search(domain)
                    operator = user_id.display_name or oper_code
                else:
                    operator = ''

                st = 90
                en = st + 14
                date_done = sga_file_obj.format_from_mecalux_date(line[st:en].strip())
                vals = {'sga_state': 'MT',
                        'pick_weight': pick_weight,
                        'pick_packages': pick_packages,
                        'carrier_id': carrier_id,
                        'operator': operator,
                        'date_done': date_done}
                if carrier.carrier_type == 'seur':
                    vals['seur_service_code'] = carrier.seur_service_code
                    vals['seur_product_code'] = carrier.seur_product_code
                pick.write(vals)
            elif len(line) == LEN_LINE and pick:
                #Buscamos la operacion relacionada
                st = 0
                en = st + 10
                op_id = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (10, 10, 0))
                op = self.env['stock.pack.operation'].search([('id', '=', op_id), ('picking_id', '=', pick.id)])
                if op_id and not op:

                    error_message = u'Op %s no encontrada en el albarán %s' % (op_id, pick.name)
                    self.create_sga_file_error(sga_file_obj, n_line,'ZCS',pick,'Op no encontrada', error_message)
                    bool_error = False
                    continue
                # cantidad a realizar
                st = 284
                en = st + 12
                qty_done = sga_file_obj.format_from_mecalux_number(line[st:en].strip() or 0, (12, 7, 5))
                if op:
                    _logger.info(">> Línea % s del albarán: %s. Producto: %s Cantidad hecha %s" % (
                    op.id, pick.name, op.product_id.default_code, qty_done))
                    op.write({'qty_done': qty_done, 'sga_changed': True})
                    sga_ops_exists = True
            else:
                continue

        if pick:
            pick.do_pick(sga_ops_exists)
        return pool_ids


    def create_sga_file_error(self, sga_file_obj, n_line, sga_operation, pick, error_code, error_message):
        error_vals = {'file_name': sga_file_obj.name,
                      'sga_file_id': sga_file_obj.id,
                      'line_number': n_line,
                      'sga_operation': sga_operation,
                      'object_type': sga_operation,
                      'object_id': pick.name,
                      'date_error': sga_file_obj.name[5:19].strip(),
                      'error_code': error_code,
                      'error_message': error_message}
        self.env['sga.file.error'].create(error_vals)
