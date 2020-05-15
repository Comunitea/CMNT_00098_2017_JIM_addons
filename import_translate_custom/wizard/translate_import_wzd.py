# -*- coding: utf-8 -*-
# © 2018 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, _
import xlrd
import base64
import logging

_logger = logging.getLogger(__name__)

# Global variable to store the new created templates
template_ids = []

class TranslateIMportError(models.TransientModel):
    _name = 'translate.import.error'

    line_id = fields.Integer ('Numero de línea')
    text = fields.Char('Linea')
    filename = fields.Char('Fichero')

class TranslateImportWzd(models.TransientModel):
    _name = 'translate.import.wzd'

    file = fields.Binary(string='File')
    lang = fields.Many2one(
        comodel_name="res.lang", string="Idioma", required=True)
    filename = fields.Char(string='Filename')

    def _parse_row_vals(self, row, idx):
        res = {
            'id': row[0],
            'template_code': row[1],
            'source': row[2],
            'name': row[3],
            'description': row[4],
            'description_sale': row[5],
            'description_purchase': row[6],
            'description_picking': row[7],
        }

        # Check mandatory values setted
        return res

    def get_ref(self, ext_id):
        ext_id_c = ext_id.split('.')
        if len(ext_id_c) == 1:
            domain = [('model', '=', 'product.product'), ('module', '=', ''), ('name', '=', ext_id)]
        else:
            domain = [('model', '=', 'product.product'), ('module', '=', ext_id_c[0]), ('name', '=', ext_id_c[1])]

        res_id = self.env['ir.model.data'].search(domain, limit=1)
        return res_id and res_id.res_id or False

    def get_res_id(self, vals):
        template = self.env['product.template']
        template_id = False

        if vals['id']:
            template_id = template.search([('id', '=', int(vals['id']))])
        if not template_id and vals['template_code']:
            domain = [('template_code', '=', '{}'.format(vals['template_code']))]
            template_ids = template.search(domain)
            if len(template_ids)==1:
                template_id = template_ids[0]

        if not template_id and vals['source']:
            ctx = {}
            domain = [('name', '=', '{}'.format(vals['source']))]
            template_ids = template.with_context(ctx).search(domain)
            if len(template_ids)==1:
                template_id = template_ids[0]

        return template_id


    def import_translate(self):
        _logger.info(_('Comienzo de la importación de traducciones'))

        # get the first worksheet
        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        idx = 2
        row_err = []
        lang_code = self.lang.code
        filename = '{}.{}'.format(lang_code, self.filename)
        field_values= [] #['id', 'lang', 'src', 'name', 'type', 'res_id', 'state']
        for col in range(3, 10):
            try:
                field_values.append(sh.row_values(1)[col])
            except:
                break
        ir_t = self.env['ir.translation']
        domain = [('filename', '=', filename)]
        self.env['translate.import.error'].search(domain).unlink()
        for nline in range(2, sh.nrows):
                self.ensure_one()
                idx += 1
                row = sh.row_values(nline)
                row_vals = self._parse_row_vals(row, idx)
                template_id = self.get_res_id(row_vals)
                template_code = '{}'.format(row_vals['template_code'])
                name =  '{}'.format(row_vals['name'])
                if not template_id:
                    row_err += [idx]
                    err_vals = {'filename': filename, 'line_id': idx, 'text': '{}'.format(row_vals)}
                    self.env['translate.import.error'].create(err_vals)
                    _logger.info(_('Error en la fila {}: Id: {}, Ref: {} , Nombre: {}'.format(idx, int(row_vals['id']), template_code, name)))
                    continue

                for field in field_values:
                    name = 'product.template,{}'.format(field)
                    if row_vals[field]:
                        domain = [('name', '=', name), ('res_id', '=', template_id.id), ('type', '=', 'model'), ('lang', '=', lang_code)]
                        value = '{}'.format(row_vals[field])
                        t_ids = ir_t.search(domain)
                        cont = len(t_ids)
                        if cont>1:
                            t_ids.unlink()
                            cont = 0
                        if cont==1:
                            t_ids.write({'state': 'translated', 'name': name, 'value': value})
                        if cont == 0:
                            vals = {'name': name,
                                    'res_id': template_id,
                                    'lang': lang_code,
                                    'state': 'translated',
                                    'type': 'model',
                                    'value': value}
                            t_ids.create(vals)
                        _logger.info(_('Línea {} de {}: Update {}. Campo {}'.format(nline, sh.nrows, template_id.name, field)))

        if len(row_err):
            return self.action_view_errors(filename)


    def action_view_errors(self, fichero):
        self.ensure_one()
        action = self.env.ref(
            'import_translate_custom.translate_import_error_tree_action').read()[0]
        action['domain'] = [('filename', '=', fichero)]
        return action
