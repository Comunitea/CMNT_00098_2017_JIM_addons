# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api
from datetime import datetime


class PurchaseForecast(models.Model):

    _name = "purchase.forecast"

    name = fields.Char('Name', required=True)
    category_id = fields.Many2one('product.category', 'Product Category',
                                  required=True)
    lines_count = fields.Float('Nº Lines', compute='_get_lines_count')
    stock_months = fields.Integer('Stock Months')

    @api.multi
    def _get_lines_count(self):
        for forecast in self:
            self.lines_count = self.env['purchase.forecast.line'].\
                search_count([('forecast_id', '=', self.id)])

    @api.multi
    def delete_forecast_lines(self):
        for forecast in self:
            domain = [('forecast_id', '=', forecast.id)]
            self.env['purchase.forecast.line'].search(domain).unlink()
        return

    @api.multi
    def unlink(self):
        self.delete_forecast_lines()
        res = super(PurchaseForecast, self).unlink()
        return res

    @api.model
    def _get_demand(self, product_id):
        return 0.0

    @api.model
    def _get_qty_year_ago(self, product_id, num_years_ago=0):
        qty = 0
        today = datetime.today()
        year = today.year - num_years_ago
        date_start = str(year) + '-' + '01' + '-' + '01'
        date_end = str(year) + '-' + '12' + '-' + '31'
        print date_start
        print date_end
        company_id = self.env.user.company_id.id
        query = """
            SELECT sum(qty)
            FROM sale_history
            WHERE date >= '%s' AND
                  date <= '%s' AND product_id = %s AND company_id = %s
            GROUP BY product_id
        """ % (date_start, date_end, product_id, company_id)

        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
        print qres
        return qty

    @api.multi
    def create_lines(self):
        self.ensure_one()
        self.delete_forecast_lines()
        products = self.env['product.product'].\
            search([('categ_id', '=', self.category_id.id)])
        for product in products:

            vals = {
                'forecast_id': self.id,
                'product_id': product.id,
                'year1_ago': self._get_qty_year_ago(product.id, 1),
                'year2_ago': self._get_qty_year_ago(product.id, 2),
                'year3_ago': self._get_qty_year_ago(product.id, 3),
                'year4_ago': self._get_qty_year_ago(product.id, 4),
                'year5_ago': self._get_qty_year_ago(product.id, 5),
                'demand': self._get_demand(product.id)
            }
            self.env['purchase.forecast.line'].create(vals)

    @api.multi
    def show_lines(self):
        self.ensure_one()
        action = self.env.ref('jim_purchase_forecast.action_forecast_lines').\
            read()[0]
        action['domain'] = [('forecast_id', '=', self.id)]
        return action


class PurchaseForecastLine(models.Model):

    _name = "purchase.forecast.line"

    forecast_id = fields.Many2one('purchase.forecast', 'Forecast')
    product_id = fields.Many2one('product.product', 'Product')
    year1_ago = fields.Float('1 Year Ago')
    year2_ago = fields.Float('2 Year Ago')
    year3_ago = fields.Float('3 Year Ago')
    year4_ago = fields.Float('4 Year Ago')
    year5_ago = fields.Float('5 Year Ago')
    demand = fields.Float('Demand')
    stock = fields.Float('Current Stock',
                         related="product_id.global_real_stock")
