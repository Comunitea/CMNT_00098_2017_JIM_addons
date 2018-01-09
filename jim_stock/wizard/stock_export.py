# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
import base64
import xlsxwriter
from StringIO import StringIO


class JimStockExport(models.TransientModel):

    _name = 'jim.stock.export'

    company = fields.Many2one('res.company')
    name = fields.Char('File Name', readonly=True)
    file = fields.Binary()

    @api.multi
    def export_stock(self):
        file_data = StringIO()
        workbook = xlsxwriter.Workbook(file_data)
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, 'ItemCode')
        worksheet.write(0, 1, 'ItemName')
        worksheet.write(0, 2, 'Location nternal id')
        worksheet.write(0, 3, 'Location')
        worksheet.write(0, 4, 'Quantity')
        worksheet.write(0, 5, 'Quantity import')
        worksheet.write(0, 6, 'WarehouseCode')
        quants = self.env['stock.quant'].read_group(
            [('company_id', '=', self.company.id),
             ('location_id.usage', '=', 'internal')],
            ['product_id', 'location_id', 'qty'],
            ['product_id', 'location_id'], lazy=False)
        row = 1
        for quant in quants:
            product = self.env['product.product'].browse(
                quant['product_id'][0])
            worksheet.write(row, 0, product.default_code)
            worksheet.write(row, 1, product.display_name)
            worksheet.write(row, 2,  quant['location_id'][0])
            worksheet.write(row, 3,  quant['location_id'][1])
            worksheet.write(row, 4, quant['qty'])
            worksheet.write(row, 5, quant['qty'])
            row += 1
        workbook.close()
        file_data.seek(0)
        self.name = 'export_%s.xlsx' % self.company.name
        self.file = base64.b64encode(file_data.read())
        return {
            "type": "ir.actions.do_nothing",
        }
