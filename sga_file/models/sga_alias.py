# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, tools, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import codecs
ENCODE = "latin_1"

class SGAAlias(models.Model):

    _name = "sga.alias"
    _description = "Mecalux Alias"

    product_id = fields.Many2one('product.product')
    alias_code = fields.Char('Alias Code')
    product_code = fields.Char(related='product_id.default_code')
    uom_id = fields.Many2one('product_uom')
    uom_code = fields.Char(related='uom_id.sga_uom_base_code')

    def import_mecalux_ALI(self, file_id):

        sga_file_obj = self.env['sga.file'].browse(file_id)
        sga_file = open(sga_file_obj.sga_file, 'r')
        no_error = True
        line_number = 0
        bom = True

        for line_d in sga_file:
            try:
                if bom:
                    line = line_d.decode(ENCODE).encode(ENCODE)
                else:
                    line = line_d

                line_number += 1
                st = 1
                en = st + 51
                alias_code = line[st:en].strip()
                st = en
                en = st + 50
                product_code = line[st:en].strip()
                st = en
                en = st + 4
                uom_code = line[st:en].strip()

                pool_alias = self.env['sga.alias']
                domain_alias = [('alias_code', '=', alias_code)]
                alias_id = pool_alias.search(domain_alias)

                domain_uom = [('sga_uom_base_code', '=', 'uom_code')]
                uom_id = self.env['product_uom'].search(domain_uom)
                if not uom_id:
                    sga_file_obj.write_log("-- ERROR >> Error Al procesar el fichero:\n%s"
                                           "\nNo encuentro la unidad %s. Comprueba los valores de la linea nº %s" % (
                                           sga_file_obj.sga_file, uom_code, line_number))
                    no_error = False
                    continue

                domain_product = [('default_code','=', product_code)]
                product_id = self.env['product.product'].search(domain_product)
                if not product_id or len(product_id)>1:
                    sga_file_obj.write_log("-- ERROR >> Error Al procesar el fichero:\n%s"
                                           "\nError en la referencia %s. Comprueba los valores de la linea nº %s" % (
                                               sga_file_obj.sga_file, product_code, line_number))
                    no_error = False
                    continue

                if alias_id:
                    self.product_id = product_id
                    self.uom_id = uom_id
                else:
                    values = {
                        'product_id': product_id.id,
                        'uom_id':uom_id.id,
                        'alias_code': alias_code
                    }
                    pool_alias.create(values)

            except:
                no_error = False

        if not no_error:
            sga_file_obj.write_log("-- ERROR >> Error Al procesar el fichero:\n%s" % (sga_file_obj.sga_file))

        sga_file.close()
        return no_error

