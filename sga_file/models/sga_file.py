# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

#El sistema puede funcionar con ficheros, sin embargo,
#creo que tiene mas rendimiento esto que andar recuperando y buscando paths y options
#TODO REVISAR CUAL ES MAS EFICIENTE
#import settings_sga_file
#IN_FOLDER = settings_sga_file.IN_FOLDER

DELETE_FILE = False
ERRORS = 3
ODOO_READ_FOLDER = 'Send'
ODOO_WRITE_FOLDER = 'Receive'

class ConfigPathFiles(models.TransientModel):

    _inherit = 'stock.config.settings'

    path_files = fields.Char('Files Path', help="Path to SGA Mecalux exchange files. Must content in, out, error, processed and history folders\nAlso a scheduled action is created: Archive SGA files")
    product_auto = fields.Boolean('Auto update productos', help="Enviar cambios en productos y clientes automaticamente al servidor", default=False)
    picking_auto = fields.Boolean("Auto validación de picks", help = "Valor por defecto para autovalidacion de Mecalux")
    inventary_auto = fields.Boolean("Auto validación de inventarios", help ="Validación automatica de ajustes de inventarios creados desde Mecalux")

    @api.model
    def get_default_path_files(self, fields):
        res = {}
        icp = self.env['ir.config_parameter']
        res['path_files'] = icp.get_param(
            'path_files')
        return res

    @api.model
    def get_default_product_auto(self, fields):
        res = {}
        icp = self.env['ir.config_parameter']
        res['product_auto'] = icp.get_param(
            'product_auto')
        return res

    @api.model
    def get_default_picking_auto(self, fields):
        res = {}
        icp = self.env['ir.config_parameter']
        res['picking_auto'] = icp.get_param(
            'picking_auto')
        return res

    @api.model
    def get_default_inventary_auto(self, fields):
        res = {}
        icp = self.env['ir.config_parameter']
        res['inventary_auto'] = icp.get_param(
            'inventary_auto')
        return res

    @api.multi
    def set_product_auto(self):
        icp = self.env['ir.config_parameter']
        icp.set_param('product_auto',
                      self.product_auto)

    @api.multi
    def set_picking_auto(self):
        icp = self.env['ir.config_parameter']
        icp.set_param('picking_auto',
                      self.picking_auto)

    @api.multi
    def set_inventary_auto(self):
        icp = self.env['ir.config_parameter']
        icp.set_param('inventary_auto',
                      self.inventary_auto)

    @api.multi
    def set_path_files(self):
        import os
        if os.path.isdir(self.path_files):
            try:
                for folder in (ODOO_READ_FOLDER, ODOO_WRITE_FOLDER, 'error', 'archive', 'zip', 'delete', 'log'):
                    new_path = "%s/%s" % (self.path_files, folder)
                    if not os.path.exists(new_path):
                        os.makedirs(new_path)
            except:
                raise UserError("Error creating directories in %s" % self.path_files)
        else:
            raise UserError("Folder not exists %s" % self.path_files)

        if self.path_files:
            icp = self.env['ir.config_parameter']
            icp.set_param('path_files',
                          self.path_files)

class MecaluxVars(models.Model):

    _name ='sgavar.file.var'
    _order = "sequence, id asc"

    sga_file_id = fields.Many2one("sgavar.file")
    sequence = fields.Integer("Sequence", defaul = 50)
    name = fields.Char("Campo Mecalux")
    odoo_name = fields.Many2one("ir.model.fields",
                                domain="[('model_id','=',odoo_model)]",
                                string="Campo Odoo (si existe)" )
    odoo_model = fields.Many2one(related="sga_file_id.odoo_model")
    length = fields.Integer("Longitud", help="Campo numerico.")
    length_int = fields.Integer("L. Entera", help="Longitud entera(nº de digitos de la parte entera en un tipo 'float')")
    length_dec = fields.Integer("L. Decimal", help="Longitud decimal(nº de digitos de la parte decimal en un tipo 'float')")
    mecalux_type = fields.Selection([('A', 'Alfanumerico'),
                                     ('N', 'Numerico'),
                                     ('B', 'Booleano'),
                                     ('D', 'Fecha'),
                                     ('V', 'Atributo/Variable'),
                                     ('L', 'one2many')])
    default = fields.Char("V. por defecto")
    fillchar = fields.Char("Caracter de relleno", size=1)
    required = fields.Boolean("Obligatorio", default=False)
    st = fields.Integer('Inicio cadena')
    en = fields.Integer('Fin cadena')


    @api.onchange('length','length_dec')
    def onchange_length(self):
        self.length_int = self.length - self.length_dec

class MecaluxFile(models.Model):

    _name = 'sgavar.file'

    def _get_name(self):
        for sgavar_file in self:
            sgavar_file.name = '%s/%s'%(sgavar_file.code, sgavar_file.version)

    name = fields.Char('Sga name', compute="_get_name")
    description = fields.Char('Sga file description')
    code = fields.Char('Sga file type', size=3)
    version = fields.Char("Version", size=2)
    odoo_model = fields.Many2one('ir.model', "Odoo Model")
    model = fields.Char(related='odoo_model.name')
    cte_name = fields.Char("Cte name")
    sga_file_var_ids = fields.One2many('sgavar.file.var', 'sga_file_id')
    version_active = fields.Boolean('Active')
    bytes = fields.Integer('Bytes')
    filter = fields.Char("Filter")
    _sql_constraints = [
        ('code_uniq', 'unique (code, version)', 'Este codigo/version de archivo ya existe!'),
    ]

    @api.constrains('version', 'version_active')
    def _check_active_version(self):
        domain = [('code', '=', self.code), ('version_active','=', True)]
        pool = self.search(domain)
        if len(pool) > 1:
            raise ValidationError("Solo puedes tener una version activa para coada codigo de fichero")

    @api.multi
    def write(self, vals):
        var_bytes = 0
        for var in self.sga_file_var_ids:
            var_bytes += var.length
        vals['bytes'] = var_bytes
        return super(MecaluxFile, self).write(vals)

    def reset_sequence(self):
        return
        domain = [('id', '!=', 0)]
        pool_files = self.env['sgavar.file'].search(domain)
        for pool in pool_files:
            min_id = 10000

            for var in pool.sga_file_var_ids:
                min_id = min(min_id, var.id)
            for var in pool.sga_file_var_ids:
                var.sequence = var.id - min_id
        return


    def update_positions(self):

        domain = [('id', '!=', 0)]
        pool_files = self.env['sgavar.file'].search(domain)
        for sga in pool_files:
            st=0
            en=0
            for var in sga.sga_file_var_ids:
                st = en
                en = st + var.length
                var.st = st
                var.en = en
        return True

class MecaluxFileHeader(models.Model):

    #Historico de ficheros donde guardar
    _name = "sga.file"

    name = fields.Char()
    sga_file = fields.Char('Fichero')  # ruta completa donde esta el archivo
    sga_path = fields.Char('Carpeta', default='', help="Carpeta del archivo")
    file_code = fields.Char('Codigo del fichero', size=3)

    state = fields.Selection([('W', 'En espera'), ('P', 'Procesado'), ('E', 'Error')])
    errors = fields.Integer('Errores', help="Numero de veces que debe aparecer el error antes de mover a error", default=1)
    file_type = fields.Selection ([(ODOO_READ_FOLDER, 'De Mecalux a Odoo'), (ODOO_WRITE_FOLDER, 'De Odoo a Mecalux')], string ="Tipo de fichero (I/O)", translate=True)

    file_time = fields.Datetime(string='Fecha/hora del archivo')
    version = fields.Integer('Version (Solo modo dev.)')

    log_name = fields.Char("Fichero log asociado")


    @api.model
    def set_file_name(self, file_type=False, version=False, file_date=False):

        if file_type and version and datetime == False:
            return False
        else:
            version = int(version)
            filename = u'%s%02d%04d%02d%02d%02d%02d%02d' %(file_type, version,
                                                           file_date.year,
                                                           file_date.month,
                                                           file_date.day,
                                                           file_date.hour,
                                                           file_date.minute,
                                                           file_date.second)
            return filename

    @api.model
    def archive_sga_files(self):
        try:
            res = True
        except:
            res = False
        return res

    @api.model
    def get_sga_type(self, sga_filename):
        if sga_filename:
            return sga_filename[0:3]
        else:
            return False

    @api.model
    def get_sga_version(self, sga_filename):
        if sga_filename:
            return sga_filename[3, 5]
        else:
            return False

    @api.model
    def get_file_time(self, sga_filename):
        try:
            return datetime(int(sga_filename[5:9]),
                            int(sga_filename[9:11]),
                            int(sga_filename[11:13]),
                            int(sga_filename[13:15]),
                            int(sga_filename[15:17]),
                            int(sga_filename[17:19]),
                            )
        except:
            return False

    @api.model
    def default_stage_id(self):
        return self.stage_id.get_default()

    def format_to_mecalux_float(self, value, length_in=(12, 7, 5), default=0, fillchar='0'):

        length, length_int, length_dec = length_in
        value = value or default
        if not value:
            val = "0" * length
            return val

        if length_dec == 0:
            # Formato entero
            val = '%s' % int(value)
            val = val.rjust(length, fillchar)
        else:
            # Formato decimal
            value = float(value)
            int_ = int(value)
            dec_ = int((value - int_) * 10 ** length_dec)
            val = str(int_).rjust(length_int, fillchar)
            val += str(dec_).ljust(length_dec, fillchar)
        return val

    def format_from_mecalux_number(self, value, length_in=(12, 7, 5), default=False, fillchar='0'):
        length, length_int, length_dec = length_in
        value = str(value)
        if length_dec > 0:
            res = value[0:length_int] + '.' + value[length_int: length_int + length_dec]
            return float(res)
        else:
            res = value[0:length_int]
            return int(res)

    def format_to_mecalux_date(self, date):

        return u'%04d%02d%02d%02d%02d%02d' % (
            date.year, date.month, date.day, date.hour, date.minute,
            date.second)

    def format_from_mecalux_date(self, mec_date, long=True):

        if not mec_date:
            return False
        if long:
            return datetime(int(mec_date[0:4]),
                            int(mec_date[4:6]),
                            int(mec_date[6:8]),
                            int(mec_date[8:10]),
                            int(mec_date[10:12]),
                            int(mec_date[12:14]))

        else:
            return datetime(int(mec_date[0:4]),
                        int(mec_date[4:6]),
                        int(mec_date[6:8]))

    def write_log(self, str_log):

        log_name = u"%04d%02d%02d.log" % (datetime.now().year, datetime.now().month, datetime.now().day)
        log_path = u'%s/%s/%s'%(self.get_global_path(), 'log', log_name)

        header = u'%s ' % datetime.now()
        if self:
            header += u'\n       %s ' % self.name

        if not os.path.exists(log_path):
            self.touch_file(log_path)
        f = open(log_path, 'a')
        if f:
            str_log = u'%s >> %s\r' %(header, str_log)
            f.write(str_log.encode('utf-8'))
            f.close()

        return True

    def get_global_path(self):

        icp = self.env['ir.config_parameter']
        path = icp.get_param('path_files', 'path_files')
        return path

    def create_new_sga_file_error(self, error_str):
        self.write_log(error_str)
        self.move_file('error')
        return False

    @api.model
    def create_new_sga_file(self, sga_filename, dest_path=ODOO_READ_FOLDER, create=True, version = 0):
        if create:
            sga_filename = '%s%02d' % (sga_filename[0:17], version)
            domain = [('name', '=', sga_filename)]
            if self.env['sga.file'].search(domain):
                version += 1
                sga_filename = '%s%02d'%(sga_filename[0:17], version)
                return self.create_new_sga_file(sga_filename, dest_path, create, version)

        path = self.get_global_path()
        sga_path = u'%s/%s'%(path, dest_path)
        error = False
        error_str = ''

        #if len(sga_filename) != 19 and len(sga_filename) != 23:
        #    error_str = u"Error en nombre de archivo: %s caracteres"% len(sga_filename)
        #    return self.create_new_sga_file_error(error_str)

        sga_file = os.path.join(sga_path, sga_filename)
        sga_type = self.get_sga_type(sga_filename)
        sga_file_time = self.get_file_time(sga_filename)
        if not sga_file_time:
            error_str = u"Error en la fecha de archivo %s " % sga_filename
            return self.create_new_sga_file_error(error_str)

        sga_state = 'W'
        vals = {
            'file_code': sga_type,
            'name': sga_filename,
            'sga_file': sga_file,
            'state': sga_state,
            'file_time': sga_file_time,
            'sga_path': sga_path,
            'log_name': u"%04d%02d%02d.log" % (datetime.now().year, datetime.now().month, datetime.now().day),
            'version': version
        }

        if create:
            error = self.touch_file(sga_file)
            if not error:
                error_str = "Error al acceder al archivo %s" % sga_file
                return self.create_new_sga_file_error(error_str)

        new_sga_file = self.create(vals)
        if not new_sga_file:
            error_str = "Error al crear SGA en la BD"
            return self.create_new_sga_file_error(error_str)

        self.write_log('Creado .... (%s)' % sga_filename)
        return new_sga_file

    @api.model
    def create(self, vals):

        sga_file = super(MecaluxFileHeader, self).create(vals)
        if sga_file:
            res = self.touch_file(sga_file.sga_file)
            if res:
                return sga_file
            else:
                raise ValidationError(_('Error al acceder/crear el archivo:\n%s.' % sga_file.sga_file))
        return sga_file

    def touch_file(self, sga_file):
        try:
            basedir = os.path.dirname(sga_file)
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            if not os.path.exists(sga_file):
                with open(sga_file, 'a'):
                    os.utime(sga_file, None)
        except:
            return False
        return True

    @api.model
    def check_sga_name(self, filename, path):
        # compruebo que el fichero no este en la bd.
        # si esta lo borro y creo uno nuevo
        self.write_log("Proceso ... (%s)" % filename)
        domain = [('name', '=', filename)]
        sga_file = self.env['sga.file'].search(domain)
        if sga_file:
            sga_file.unlink()
        sga_file = self.create_new_sga_file(filename, ODOO_READ_FOLDER, create=False)
        if not sga_file:
            error_str = 'Error al crear %s en la BD' % filename
            sga_file.write_log(error_str)
            return False

        return sga_file

    def import_file_from_mecalux(self):

        process = []
        proc_error = False

        if self.file_code=="CSO":
            self.write_log("Desde mecalux picking CSO ...")
            process = self.env['stock.picking'].import_mecalux_CSO(self.id)

        elif self.file_code == "ZCS":
            self.write_log("Desde mecalux picking ZCS ...")
            process = self.env['stock.picking'].import_mecalux_ZCS(self.id)

        elif self.file_code == 'STO':
            self.write_log("Desde mecalux inventory STO ...")
            process = self.env['stock.inventory'].import_inventory_STO(self.id)

        elif self.file_code == 'CRP':
            self.write_log("Desde mecalux picking CRP ...")
            process = self.env['stock.picking'].import_mecalux_CRP(self.id)

        elif self.file_code == 'EIM':
            self.write_log("Desde mecalux error EIM ...")
            process = self.env['sga.file.error'].import_mecalux_EIM(self.id)

        try:
            if process:
                self.write_log("-- OK >> %s" % self.sga_file)
                self.move_file('archive', self.name)
            else:
                proc_error = True

        except:
            proc_error = True
        if proc_error:
            self.errors += 1
            self.write_log("-- ERROR >> %s" % self.sga_file)
            self.move_file('error', self.name)
        return process

    #este es la accion que recorre la carpeta de ficheros provenientes del SGA
    def sga_process_file_xmlrpc(self):
        return self.process_sga_files()

    def process_sga_files(self, file_type=False, folder=ODOO_READ_FOLDER):

        res_file = False
        global_path = u'%s/%s' %(self.get_global_path(), folder)
        self.write_log("Buscando ficheros en >> %s" % global_path)
        pool_ids=[]
        for path, directories, files in os.walk(global_path, topdown=False):
            for name in files:
                if file_type:
                    if name[0:3] != file_type:
                        continue
                sga_file = self.check_sga_name(name, path)
                if sga_file:
                    # lo proceso
                    pool_id = sga_file.import_file_from_mecalux()
                    if pool_id:
                        pool_ids += pool_id

        #Si solo hay un tipo de fichero , devuelvo los ids, si no True
        if pool_ids:
            pool_ids = pool_ids if file_type else True

        return pool_ids

    def move_file(self, folder, file_name=False):
        new_path = False
        try:
            new_path = u'%s/%s' % (self.get_global_path(), folder)
            new_name = os.path.join(new_path, self.name)
            os.rename(self.sga_file, new_name)
            self.sga_file = new_name
            self.sga_path = new_path
            self.write_log("-- Movemos  >> %s a %s" %(self.name, new_path))
        except:
            self.write_log("-- Error al mover >> %s a %s" %(self.name, new_path))

    @api.multi
    def check_sga_file(self, model, ids=[], code=False, create=True):
        # code = False,  version = False, field_list = False, field_ids = False, field_list_ids = False):
        # model modelo principal
        # ids si se especifica recorre solo estos id,
        # create fuerza la creacion del fichero
        # code codigo de aplicacion del fichero
        # version version del fichero
        # field_list lista de campos/longitud que a generar

        # field_ids si tiene lista de filas (sale_order_line estan en este campo
        # con la lista de campos/longitud field_list_ids

        def get_line(sgavar, model_pool):
            # TODO Revisar si hace falta contador para los
            # todo numeros de lineas o vale el id de los _ids
            cont = 0
            res = ''
            line_ids = False
            if sgavar.filter:
                model_pool = model_pool.filtered(eval(sgavar.filter))
            for model in model_pool:

                cont += 1
                model_str = ''
                var_str = ''
                new_sga_file.write_log('--> Modelo %s'%model)

                for val in sgavar.sga_file_var_ids:

                    value = False
                    length = [val.length, val.length_int, val.length_dec]

                    # Si viene en el context forzada la variable
                    if self._context.get(val.name, False):
                        var_str = self.odoo_to_mecalux(self._context.get(val.name),
                                                       length, val.mecalux_type, val.default, val.fillchar)

                    # Si es un atributo >>> debe tener asignado un campo en odoo o es []
                    elif val.mecalux_type == "V":
                        if val.odoo_name:
                            value = u'[%s]' % model[val.odoo_name.name]
                        else:
                            value = u'[]'
                        var_str = value

                    # No es Listado de lineas
                    elif val.mecalux_type != "L":
                        if val.name == "line_number" and not val.odoo_name:
                            value = cont
                        elif val.odoo_name:
                            value = model[val.odoo_name.name]

                        if not value and val.required:
                                value = val.default

                        if value == '' and not val.default:
                            raise UserError("Revisa la configuracion del campo %s del modelo %s"%(val.name, val.sga_file_id))

                        var_str = self.odoo_to_mecalux(value, length, val.mecalux_type, val.default, val.fillchar)
                    else:
                        # Listado de lineas
                        new_model = model[val.odoo_name.name]
                        new_sgavar = self.env['sgavar.file'].search([('code', '=', val.default)], limit=1)
                        if new_sgavar.filter:
                            new_model = new_model.filtered(eval(new_sgavar.filter))
                        value = len(new_model) or 0
                        var_str = self.odoo_to_mecalux(value, length, val.mecalux_type, val.default, val.fillchar)
                        line_ids = True

                    model_str += var_str
                res += model_str + '\n'

                if line_ids:
                    res += get_line(new_sgavar, new_model)
            return res

        domain = [('code', '=', code)]
        sgavar = self.env['sgavar.file'].search(domain)
        if not sgavar:
            return
            raise ValidationError("No se ha encontrado un modelo para ese tipo de fichero %s" % code)

        if not ids:
            return
            raise ValidationError("No se ha encontrado ningun registro para procesar")
        model_pool = self.env[model].browse(ids)

        if not model_pool:
            raise ValidationError("No se ha encontrado ningun registro de %s" % model)

        data_file = datetime.now()
        sga_file_name = self.set_file_name(sgavar.code, sgavar.version, data_file)
        if not sga_file_name:
            raise ValidationError("Error en el nombre del fichero")

        new_sga_file = self.create_new_sga_file(sga_file_name, ODOO_WRITE_FOLDER, create=create)

        if not new_sga_file:
            raise ValidationError("Error. Revisa el fichero del log para mas detalles")
        new_sga_file.write_log('Compruebo fichero ...')

        if new_sga_file:
            f = open(new_sga_file.sga_file, 'a')
            if f:
                file_str = get_line(sgavar, model_pool)
                f.write(file_str.encode("latin_1"))
                f.close()
            else:
                raise ValidationError("Error al escribir los datos en %s" % new_sga_file.sga_file)

        return new_sga_file

    def odoo_to_mecalux(self, value, length_in, type, default=False, fillchar=False):


        def type_A(value):
            # Tipo string
            if not default and not value:
                val = " " * length_int
            else:
                new_val = '%s' %(value or default)
                val = new_val.ljust(length_int, fillchar)
            return val

        def type_B(value):
            # Tipo string
            if value == "1" or value is True:
                new_val = "1"
            elif value == "0" or value is False:
                new_val = "0"
            else:
                new_val = " "
            return new_val

        def type_N(value):

            val = self.format_to_mecalux_float(value, length_in)
            return val

        length, length_int, length_dec = length_in
        fillchar = str(fillchar)

        if type == 'A':
            # Mecalux alphanumeric
            return type_A(value)[0:length_int]

        elif type == 'B':
            # Mecalux Boolean
            if value == "":
                value == default or fillchar

            return type_B(value)

        elif type == 'N':
            # Mecalux Numeric
            return type_N(value)

        elif type == 'L':
            # One2many, pero es Mecalux Numeric
            return type_N(value)

        elif type == "D":
            if value:
                value = self.format_to_mecalux_date(datetime.strptime(value, tools.DEFAULT_SERVER_DATETIME_FORMAT))
            else:
                value = ''
            # Mecalux date
            return type_A(value)

        elif type == "V":
            # Mecalux Atribute
            return ''
        else:
            return ''

class MecaluxFileLine(models.Model):
    _name = "sga.file.line"

    sga_file_id = fields.Many2one('sga.file')
    stock_move_id = fields.Many2one("stock.move")
    line = fields.Char('File line')
    name = fields.Char('Line name')




