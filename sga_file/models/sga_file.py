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

IN_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/in'
OUT_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/out'
ERROR_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/error'
DELETE_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/delete'
ARCHIVE_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/archive'
ZIP_FOLDER = ''
DELETE_FILE = False
ERRORS = 3


def format_to_mecalux_date(date):
    return u'%04d%02d%02d%02d%02d%02d' % (
        date.year, date.month, date.day, date.hour, date.minute,
        date.second)


def get_file_time(sga_filename):
    if sga_filename:
        return datetime(int(sga_filename[5:9]),
                        int(sga_filename[9:11]),
                        int(sga_filename[11:13]),
                        int(sga_filename[13:15]),
                        int(sga_filename[15:17]),
                        int(sga_filename[17:19]),
                        )
    else:
        return False




class PathFiles(models.TransientModel):

    _inherit = 'stock.config.settings'

    path_files = fields.Char('Files Path', help="Path to SGA Mecalux exchange files. Must content in, out, error, processed and history folders\nAlso a scheduled action is created: Archive SGA files")

    @api.model
    def get_default_path_files(self, fields):
        res = {}
        icp = self.env['ir.config_parameter']
        res['path_files'] = icp.get_param(
            'path_files', 'path_files'
        )
        return res

    @api.multi
    def set_path_files(self):
        if self.path_files:
            icp = self.env['ir.config_parameter']
            icp.set_param('path_files',
                          self.path_files)



class ModelSgafileVar(models.Model):

    _name ='sgavar.file.var'
    _order = "sequence, id asc"

    sequence = fields.Integer("Sequence", defaul = 50)
    name = fields.Char("Mecalux field")
    odoo_name = fields.Many2one("ir.model.fields", domain="[('model_id','=',odoo_model)]", string="Odoo field" )
    odoo_many_name = fields.Char(string="Odoo Many - field",
                                help="if odoo _name is many field, get the field in related model")
    odoo_model = fields.Many2one(related="sga_file_id.odoo_model")
    length = fields.Integer("Length", help="Numeric field.")
    length_int = fields.Integer("Length Int", help="Length (Int part of float number)")
    length_dec = fields.Integer("Length Dec", help="Length (dec part of float number)")
    mecalux_type = fields.Selection([('A', 'Alfanumerico'), ('N', 'Numerico'),
                                    ('B', 'Booleano'), ('D', 'Fecha'), ('V', 'Atributo/Variable'), ('L', '2many')])
    default = fields.Char("Default Value")
    fillchar = fields.Char("Char to fill", size=1)
    sga_file_id = fields.Many2one("sgavar.file")

    @api.onchange('length','length_dec')
    def onchange_length(self):
        self.length_int = self.length - self.length_dec



class ModelSgafile(models.Model):

    _name = 'sgavar.file'


    def _get_name(self):
        for sgavar_file in self:
            sgavar_file.name = '%s/%s'%(sgavar_file.code, sgavar_file.version)

    name = fields.Char('Sga name', compute="_get_name")
    description = fields.Char('Sga file description')
    code = fields.Char('Sga file type', size=3)
    version = fields.Char("Version", size=2)
    odoo_model = fields.Many2one('ir.model', "Odoo Model")
    model = fields.Char(related = 'odoo_model.name')
    cte_name = fields.Char("Cte name")
    sga_file_var_ids = fields.One2many('sgavar.file.var','sga_file_id')
    version_active = fields.Boolean('Active')
    bytes = fields.Integer('Bytes')

    _sql_constraints = [
        ('code_uniq', 'unique (code, version)', 'Este codigo/version de archivo ya existe!'),

    ]

    @api.constrains('version', 'version_active')
    def _check_active_version(self):
        domain = [('code','=', self.code), ('version_active','=', True)]
        pool = self.search(domain)
        if len(pool) > 1:
            raise ValidationError("You have yet a version active for this code")

    @api.multi
    def write(self, vals):
        var_bytes = 0
        for var in self.sga_file_var_ids:
            var_bytes += var.length
        vals['bytes'] = var_bytes
        return super(ModelSgafile, self).write(vals)

    def reset_sequence(self):

        domain = [('id', '!=', 0)]
        pool_files = self.env['sgavar.file'].search(domain)

        for pool in pool_files:
            min_id = 10000
            print "Actuializando %s" % pool.code
            for var in pool.sga_file_var_ids:
                min_id = min(min_id, var.id)
            for var in pool.sga_file_var_ids:
                var.sequence = var.id - min_id
                print ">>>>>>%s (%s) a sequence %s" % (var.name, var.id, var.sequence)

        return

class SGAFiles(models.Model):

    #Historico de ficheros donde guardar
    _name = "sga.file"

    name = fields.Char()
    sga_file = fields.Char('Data File')  # ruta completa donde esta el archivo
    sga_path = fields.Char('File path', default='', help="File folder. Zip file if archived")
    file_code = fields.Selection([('TPR', 'Product type'), ('DEF', 'Default')])

    state = fields.Selection([('W', 'Waiting'), ('P', 'Processed'), ('E', 'Error')])
    errors = fields.Integer('Errors', help="Number of errors before move to error folder", default=1)
    type = fields.Selection ([('in', 'In'), ('out', 'Out')], string ="File type", translate=True)

    file_time = fields.Datetime(string='File date/time')
    version = fields.Integer('Version Control (Only dev mode)')

    @api.model
    def set_file_name(self, type = False, version = False, file_date = False):

        if type and version and datetime == False:
            return False
        else:
            filename = u'%s%s%04d%02d%02d%02d%02d%02d' %(type, version, file_date.year, file_date.month, file_date.day, file_date.hour, file_date.minute, file_date.second)
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
            return sga_filename[3,5]
        else:
            return False

    @api.model
    def get_file_time(self, sga_filename):

        if sga_filename:
            return datetime(int(sga_filename[5:9]),
                            int(sga_filename[9:11]),
                            int(sga_filename[11:13]),
                            int(sga_filename[13:15]),
                            int(sga_filename[15:17]),
                            int(sga_filename[17:19]),
                            )
        else:
            return False

    @api.model
    def default_stage_id(self):
        return self.stage_id.get_default()


    @api.model
    def create_new_sga_file(self, sga_filename, dest_path = 'in', create = True):
        ##import ipdb; ipdb.set_trace()
        icp = self.env['ir.config_parameter']
        path = icp.get_param(
            'path_files', 'path_files'
        )
        sga_path = u'%s/%s'%(path, dest_path)
        sga_file = os.path.join(sga_path, sga_filename)
        sga_type = self.get_sga_type(sga_filename)
        sga_file_time = self.get_file_time(sga_filename)
        sga_state = 'W'
        vals = {
            'code': sga_type,
            'name': sga_filename,
            'sga_file': sga_file,
            #'type' : dest_path,
            'state': sga_state,
            'file_time': sga_file_time,
            'sga_path': sga_path
        }
        print vals
        new_sga_file = self.create(vals)

        #creo el fichero a aunque sea vacio
        if create and new_sga_file:
            self.touch(sga_file)

        return new_sga_file

    @api.model
    def create(self, vals):
        ##import ipdb; ipdb.set_trace()

        sga_file = super(SGAFiles, self).create(vals)
        if sga_file:
            res = self.touch(sga_file.sga_file)
            if res:
                return sga_file
            else:
                raise ValidationError(_('Error ! SGA file object cant be created because not file created.'))
        return sga_file


    def touch(self, sga_file):


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


    def check_sga_name_xmlrpc(self):
        filename = self._context.get('xmlrpc_filename', False)
        path = self._context.get('xmlrpc_path', False)

        sga_file, new = self.check_sga_name(filename, path)
        res ={'sga_file':sga_file.id,
              'new': new}
        return res

    def format_to_mecalux_date(self, date):

        return u'%04d%02d%02d%02d%02d%02d' % (
        date.year, date.month, date.day, date.hour, date.minute,
        date.second)


    @api.model
    def check_sga_name(self, filename, path):
        domain = [('name', '=', filename)]
        sga_file = self.env['sga.file'].search(domain)
        new = False
        if not sga_file:
            sga_file = self.create_new_sga_file(filename, 'in', create = False)
            new = True
        if not sga_file:
            raise ValidationError(_('Error ! SGA file object cant be created.'))
        return sga_file, new

    def process_header(self, line):
        #Aqui proceso la cabecera
        self.text = line.split(',')[0]

        return True

    def process_line(self, line, line_number):

        #procesamos una linea: sga_fiel_line
        #res = self.file_line_ids.process_line(line)
        vals = {'name': '%s [%s]'%(self.name, line_number),
                'sga_file_id': self.id,
                'line': line
                }
        print "Creo linea con %s"%vals
        res = self.file_line_ids.create(vals)
        return  res


    def sga_process_file_xmlrpc(self):
        return self.sga_process_file(self._context.get('header_only', False))


    def get_stage(self, stage_name):
        res = self.env['sga.file.stage'].search([(stage_name,'=',True)], limit=1).id
        return res and res.id



    def sga_process_file(self, header_only=False):
        #procesar el archivo
        #lo abro y lo leo
        #primera linea es cabecera (si, no)
        print "Proceso archivo %s"%self.file_name
        ##import ipdb; ipdb.set_trace()
        try:
            sga_file = open(self.file_path, 'r')
            sga_file_lines = sga_file.readlines()
            sga_file.close()
            print "proceso estas lineas %s"%sga_file_lines
            res = False

            line_number = 0
            new_sga_file_line_ids = self.env['sga.file.line']

            first = True
            if first:
                line_number += 1
                line = sga_file_lines[0]
                res_header = self.process_header(line)
                self.stage_id = self.get_stage('process_stage')

            if not header_only:
                for line in sga_file_lines[1:]:
                    line_number += 1
                    res = self.process_line(line, line_number)
                    if res:
                        new_sga_file_line_ids += res
                self.stage_id = self.get_stage('archive_stage')
                self.file_line_ids = [(6, 0, new_sga_file_line_ids.ids)]
                #lo movemos si procede ....
                new_name = os.path.join(ARCHIVE_FOLDER, self.name)
                print "Movemos de %s a %s" % (new_name, self.file_path)
                os.rename(self.file_path, new_name)
                ##import ipdb; ipdb.set_trace()
                self.file_path = new_name


        except:
            print "ERROR -------------------"
            self.errors += self.errors
            if self.errors == ERRORS:
                new_name = os.path.join(ERROR_FOLDER, self.name)

        return True




    #este es la accion que recorre la carpeta de ficheros provenientes del SGA
    @api.model
    def process_sga_files(self, process = True):

        print "Recorremos directorio: %s"%IN_FOLDER
        print "Ficheros:"
        res_file = False
        for path,dir,files in os.walk(IN_FOLDER, topdown=False):
            for name in files:
                print ">>>%s"%name
                sga_file, new = self.check_sga_name(name, path)
                print "Encuentro o creo %s"%sga_file

                if new:
                    res_file = sga_file.sga_process_file(header_only=process)
                elif process:
                    res_file = sga_file.sga_process_file()

        return res_file

    def get_folders(self):
        #in_folder, out_folder, error_folder, delete_folder, archive_folder, delete_file = self.get_folders()
        return IN_FOLDER, OUT_FOLDER, ERROR_FOLDER, DELETE_FOLDER, ARCHIVE_FOLDER, DELETE_FILE


    def save_file(self, name, value):
        path = os.path.abspath(os.path.dirname(__file__))
        path += '/icecat/%s' % name
        path = re.sub('wizard/', '', path)
        f = open(path, 'w')
        try:
            f.write(value)
        finally:
            f.close()
        return path

    def check_folder(self, path=[]):
        for file in path:
            try:
                res = True
            except:
                res = False
            return res

    def read_sga_file(self, file):
        try:
            res = True
        except:
            res=False
        return res

    def write_sga_file(self, file):
        try:
            res = True
        except:
            res=False
        return res


    def move_sga_file(self, file, to_path):
        try:
            res = True
        except:
            res=False
        return res


    def process_file(self, file):
        try:
            res = True
        except:
            res = False
        return res


    def zipped_file(self, files):
        try:
            res = True
        except:
            res = False
        return res

    def archive_sga_files(self):
        try:
            res = True
        except:
            res = False
        return res



    @api.multi
    def sga_file_generate(self, code, ids=[], create=True):

        domain = [('code', '=', code)]
        sga_file = self.env['sga.file'].search(domain)
        sga_file.check_sga_file(sga_file.odoo_model, ids=ids, create=create)#,
                                #code=code, version=sga_file.version,
                                #field_list=sga_file.sga_file_var_ids,
                                #field_ids=False, field_list_ids=False)
        return True

    @api.multi
    def check_sga_file(self, model, ids = [], code = False, create = True):
        # code = False,  version = False, field_list = False, field_ids = False, field_list_ids = False):
        # model modelo principal sale_order
        # ids si se especifica recorre solo estos id, si no busca por dominio, y si no todos
        # create fuerza la creacion del fichero
        # code codigo de aplicacion del fichero
        # version version del fichero
        # field_list lista de campos/longitud que a generar

        # field_ids si tiene lista de filas (sale_order_line estan en este campo
        # con la lista de campos/longitud field_list_ids


        def get_val_line(val, model):


            meca_field = val.name

            if meca_field=='product_code':
                import ipdb; ipdb.set_trace()
            length = [val.length, val.length_int,  val.length_dec]
            fillchar = val.fillchar
            type_field = val.mecalux_type
            default_value = val.default

            odoo_field = val.odoo_name.name
            # meca_field = meca_field in model.fields_get_keys() and model.fields_get()[meca_field]

            # Si el campo no es de odoo, rellena con lo que sea necesario
            if not odoo_field:
                res = self.odoo_to_mecalux(False, length, type_field, default_value, fillchar)
                return res

            # Si el campo esta en odoo:
            if 'many' in type_field:
                # Si es un campo many ... voy a intentar evitar esto efiniendo related en los modelos
                value = model[odoo_field] and model[odoo_field][val.odoo_many_name] or False
            else:
                value = model[odoo_field]

            res = self.odoo_to_mecalux(value, length, type_field, default_value, fillchar)
            return res

        def get_line(sgavar, model_pool):
            for model in model_pool:
                more = False
                model_str=''
                var_str = ''
                for val in sgavar.sga_file_var_ids:

                    if val.name=='container_height':
                        import ipdb; ipdb.set_trace()
                    if val.mecalux_type != "L":
                        var_str = get_val_line(val, model)
                    else:

                        new_model = model_pool[val.odoo_name.name]
                        new_sgavar = self.env['sgavar.file'].search([('code', '=', val.default)], order="version desc", limit=1)
                        if len(new_model) > 0:
                            more = True
                            var_str = self.odoo_to_mecalux(False, (10, 10, 0), 'N', len(new_model), '0')
                        else:
                            var_str = self.odoo_to_mecalux(False, (10, 10, 0), 'N', 0, '0')
                    print "-----------------------Evaluamos %s con resultado %s"%(val.name, var_str)
                    model_str += var_str
                f.write(model_str + "\n")
                if more:
                    var_str_ids = get_line(new_sgavar, new_model)
            return True

        domain = [('code', '=', code)]
        sgavar = self.env['sgavar.file'].search(domain)
        if not sgavar:
            raise  "No se ha encontrado"

        model_pool = self.env[model].browse(ids)

        sga_file = self.env['sga.file']
        data_file = datetime.now()
        sga_file_name = self.set_file_name(sgavar.code, sgavar.version, data_file)
        new_sga_file = self.create_new_sga_file(sga_file_name, 'out', create=create)


        if new_sga_file:
            f = open(new_sga_file.sga_file, 'w')
            if f:
                get_line(sgavar, model_pool)
                f.close()

        return new_sga_file

    def odoo_to_mecalux(self, value, length_in, type, default, fillchar):
        # formatea el valor value segun la longitud de la cadena y el tipo de variable de mecalux
        # print type, value, length


        def type_A(value):
            #Tipo string
            if not default and not value:
                val = " " * length_int
            else:
                new_val = '%s' %(value or default)
                val = new_val.ljust(length_int, fillchar)
            return val

        def type_B(value):
            #Tipo string
            if value == "1" or value == True:
                new_val = "1"
            else:
                new_val = "0"

            #val = new_val.ljust(length_int, fillchar)
            return new_val

        def type_N(value):

            if not value:
                if not default:
                    val = "0" * length
                    return val
                else:
                    value = default

            if length_dec == 0:
                # Formato de entero
                value = int(value)
                new_val = '%s' % value
                val = new_val.rjust(length, fillchar)
            else:
                # Formato decimal
                value = float(value)
                #import ipdb; ipdb.set_trace()
                int_ = int(value)
                dec_ = int((value - int_) * 10**length_dec)
                int_ = str(int_)
                dec_ = str(dec_)
                val = int_.rjust(length_int, fillchar)
                val += dec_.ljust(length_dec, fillchar)
            print "-------------Devuelvo %s"%val
            return val

        length, length_int, length_dec = length_in

        print "Longitud: %s,%s,%s" %(length_int, length_dec, length)

        fillchar = str(fillchar)

        if type == 'A':
            # Mecalux alphanumeric
            return type_A(value)

        elif type == 'B':
            # Mecaluc Boolean
            return type_B(value)

        elif type == 'N':
            # Mecalux Numeric
            return type_N(value)

        elif type == "D":
            fillchar = ' '
            if value:
                value = self.format_to_mecalux_date(datetime.strptime(value, tools.DEFAULT_SERVER_DATETIME_FORMAT))
            else:
                value= ''
            # Mecalux date
            return type_A(value)

        elif type == "V":
            # Mecalux Atribute
            return ''
        else:
            return ''


class SGAfilesline(models.Model):
    _name = "sga.file.line"

    sga_file_id = fields.Many2one('sga.file')
    stock_move_id = fields.Many2one("stock.move")
    line = fields.Char('File line')
    name = fields.Char('Line name')



