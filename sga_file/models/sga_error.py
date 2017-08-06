# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, tools, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import codecs

class SGAfileerror(models.Model):

    _name = "sga.file.error"

    sga_file_id = fields.Many2one('sga.file')

    file_name = fields.Char(string='Fichero', size=10)
    line_number = fields.Integer('Linea')
    sga_operation = fields.Selection([('A', 'Alta'), ('M', 'Modificacion'),
                                      ('B', 'Baja'), ('F', 'Modificacion + Alta')], default='A')
    object_type = fields.Char('Tipo de objeto', size=3)
    version = fields.Integer('version')
    object_id = fields.Char("Id del objeto", size=50)
    error_code = fields.Char('Codigo de error')
    error_message = fields.Char("Mensaje de error")
    date_error = fields.Char('Fecha')
    ack = fields.Boolean("Ack", default=False)

    def confirm_ack(self):
        self.write({'ack': True})

    def import_mecalux_EIM(self, file_id):

        error_obj = self.env['sga.file.error']
        sga_file_obj = self.env['sga.file'].browse(file_id)

        sga_file = open(sga_file_obj.sga_file, 'r')
        no_error = True

        line_number = 0
        val = {}
        pool_ids = []
        bom = True
        for line_d in sga_file:
            try:
                if bom:
                    line = line_d.decode("utf-8-sig").encode("utf-8")
                else:
                    line = line_d

                line_number += 1
                val['sga_file_id'] = sga_file_obj.id

                st = 0
                en = st + 50
                val['file_name'] = line[st:en].strip()
                st = en
                en = st + 10
                val['line_number'] = int(line[st:en].strip())
                st = en
                en = st + 1
                val['sga_operation'] = line[st:en].strip()

                st = en
                en = st + 3
                val['object_type'] = line[st:en].strip()

                st = en
                en = st + 2
                val['version'] = line[st:en].strip()

                st = en
                en = st + 50
                val['object_id'] = line[st:en].strip()

                st = en
                en = st + 5
                val['error_code'] = line[st:en].strip()

                st = en
                en = st + 255
                val['error_message'] = line[st:en].strip()

                st = en
                en = st + 14
                val['date_error'] = line[st:en].strip()
                new_error = error_obj.create(val)
                pool_ids.append(new_error)

            except:

                sga_file_obj.write_log("-- ERROR >> Error Al procesar el fichero:\n%s"
                                "\nComprueba los valores de la linea nº %s"% (sga_file_obj.sga_file, line_number))

        sga_file.close()
        return pool_ids

