# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PickingGroupedInvoiceParser(models.AbstractModel):
    _name = 'report.custom_documents.report_picking_grouped_invoice'

    def _get_line_data(self, line, custom_qty=False):
        data_dict = {
            'default_code': line.product_id.default_code,
            'name': line.name,
            'price_unit': line.price_unit,
            'discount': line.discount,
        }
        if custom_qty:
            data_dict['quantity'] = custom_qty
            data_dict['price_subtotal'] = line.get_custom_qty_price(custom_qty)
        else:
            data_dict['quantity'] = line.quantity
            data_dict['price_subtotal'] = line.price_subtotal
        return data_dict

    @api.model
    def render_html(self, docids, data=None):
        invoice_lines = {}
        for invoice in self.env['account.invoice'].browse(docids):
            invoice_lines[invoice.id] = {}
            for line in invoice.invoice_line_ids:
                if len(line.mapped('move_line_ids.picking_id')) > 1:
                    moves_picking_dict = self.env['stock.move'].read_group([
                        ('invoice_line_id', '=', line.id)], ['picking_id', 'product_uom_qty'], ['picking_id'])
                    for picking_qty in moves_picking_dict:
                        picking = self.env['stock.picking'].browse(picking_qty['picking_id'][0])
                        qty = picking_qty['product_uom_qty']
                        invoice_lines[invoice.id].setdefault(picking, [])
                        invoice_lines[invoice.id][picking].append(self._get_line_data(line, qty))
                elif len(line.mapped('move_line_ids.picking_id')) == 1:
                    picking = line.mapped('move_line_ids.picking_id')
                    invoice_lines[invoice.id].setdefault(picking, [])
                    invoice_lines[invoice.id][picking].append(self._get_line_data(line))
                else:
                    invoice_lines[invoice.id].setdefault(False, [])
                    invoice_lines[invoice.id][False].append(self._get_line_data(line))
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs': self.env['account.invoice'].browse(docids),
            'invoice_lines_dict': invoice_lines,
        }
        return self.env['report'].render('custom_documents.report_picking_grouped_invoice', docargs)
