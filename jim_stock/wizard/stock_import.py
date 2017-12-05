# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import xlrd
import StringIO


class JimStockImport(models.TransientModel):

    _name = 'jim.stock.import'

    import_file = fields.Binary('File to import', required=True)

    @api.multi
    def import_stock(self):
        file = base64.b64decode(self.import_file)
        data = xlrd.open_workbook(file_contents=StringIO.StringIO(file).read())
        sh = data.sheet_by_index(0)
        in_out = self.env['stock.in.out'].create({})
        for line in range(1, sh.nrows):
            row = sh.row_values(line)
            if not row[0] or not row[2] or not row[3]:
                continue
            product_code = row[0]
            qty = float(row[3])
            if qty <= 0:
                continue
            warehouse_code = row[4]
            product = self.env['product.product'].search(
                [('default_code', '=', product_code)])
            if not product:
                raise UserError(_('Product with code %s not found') %
                                product_code)
            warehouse = self.env['stock.warehouse'].search(
                [('code', '=', warehouse_code)])
            if not warehouse:
                raise UserError(_('Warehouse with code %s not found') %
                                warehouse_code)

            new_line = self.env['stock.in.out.line'].create({
                'product': product.id,
                'quantity': qty,
                'warehouse': warehouse.id,
                'in_out': in_out.id

            })
            new_line.onchange_warehouse()
            new_line.onchange_product()
        return {'type': 'ir.actions.act_window_close'}
