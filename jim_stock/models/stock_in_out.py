# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockInOut(models.Model):

    _name = 'stock.in.out'

    name = fields.Char('Description')
    type = fields.Selection(
        (('in', 'In'), ('out', 'Out')), required=True)
    date = fields.Date()
    lines = fields.One2many('stock.in.out.line', 'in_out')
    state = fields.Selection(
        (('draft', 'Draft'), ('confirmed', 'Confirmed')), default='draft')
    company = fields.Many2one('res.company',
                              default=lambda r: r.env.user.company_id.id)

    def action_confirm(self):
        self.state = 'confirmed'
        self.lines.move_stock()


class StockInOutLine(models.Model):

    _name = 'stock.in.out.line'

    in_out = fields.Many2one('stock.in.out')
    product = fields.Many2one('product.product')
    quantity = fields.Float()
    warehouse = fields.Many2one('stock.warehouse')
    location = fields.Many2one('stock.location')
    cost_price = fields.Float()

    @api.onchange('warehouse')
    def onchange_warehouse(self):
        for line in self.filtered(lambda x: x.in_out.type == 'out'):
            if line.warehouse:
                line.location = line.warehouse.lot_stock_id

    @api.onchange('product')
    def onchange_product(self):
        for line in self:
            if line.product.seller_ids:
                cost = line.product.seller_ids[0].price
                for supplier in line.product.seller_ids:
                    if supplier.price < cost:
                        cost = supplier.price
                line.cost_price = cost

    def move_stock(self):
        for line in self:
            line.product.move_stock_import(
                line.location, line.quantity, line.cost_price,
                line.in_out.date, line.in_out.company, line.in_out.type)
