# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, tools, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import codecs
IGNORED_CODES = ('20992')

class SGAfileerror(models.Model):

    _name = "sga.file.error"

    sga_file_id = fields.Many2one('sga.file')

    file_name = fields.Char(string='Fichero', size=50)
    line_number = fields.Char('Linea')
    sga_operation = fields.Char("Operacion")
    object_type = fields.Char('Tipo de objeto', size=3)
    version = fields.Char('version')
    object_id = fields.Char("Id del objeto", size=50)
    error_code = fields.Char('Codigo de error')
    error_message = fields.Char("Mensaje de error")
    date_error = fields.Char('Fecha')
    ack = fields.Boolean("Ack", default=False)
    note = fields.Text("File line")

    def confirm_ack(self):
        self.write({'ack': True})

    def import_mecalux_EIM(self, file_id):

        error_obj = self.env['sga.file.error']
        sga_file_obj = self.env['sga.file'].browse(file_id)

        sga_file = open(sga_file_obj.sga_file, 'r')
        pool_ids =[]

        line_number = 0
        val = {}
        res = False
        bom = False
        inc = 1
        for line_d in sga_file:
            try:
                if bom:
                    line = line_d.decode("latin_1").encode("latin_1")
                else:
                    line = line_d
                line_number += 1
                val['sga_file_id'] = sga_file_obj.id
                inc = 1 if line_number == 1 else 0
                st = 2 + inc
                en = st + 25
                val['file_name'] = line[st:en].strip()
                if len(val['file_name']) != 19:
                    st = inc
                    en = st + 25
                    val['file_name'] = line[st:en].strip()
                st = en +25
                en = st + 10
                val['line_number'] = (line[st:en].strip())
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
                if val['error_code'] in IGNORED_CODES:
                    continue
                #self.refresh_sga_state(val['object_type'], val['object_id'])
                st = en
                en = st + 255
                val['error_message'] = line[st:en].strip()

                st = en
                en = st + 14
                val['date_error'] = line[st:en].strip()
                val['note'] = line
                error_file = error_obj.search([('file_name', '=', val['file_name']), ('error_code', '=', val['error_code'])])
                if not error_file:
                    error_file = error_obj.create(val)
                    self.refresh_sga_state(val['object_type'], val['object_id'], line)
                pool_ids.append(error_file.id)
            except:
                sga_file_obj.write_log("-- ERROR >> Error Al procesar el fichero:\n%s"
                                "\nComprueba los valores de la linea %s"% (sga_file_obj.sga_file, line_number))

        sga_file.close()
        return pool_ids

    def refresh_sga_state(self, object_type, object_name, line):
        if object_type in ('PRE', 'SOR'):
            domain = [('name', '=', object_name)]
            object = self.env['stock.picking'].search(domain)
            if object:
                object.message_post(body="Pick <em>%s</em> <b>Error en </b>.\n%s" % (object.name, line))
