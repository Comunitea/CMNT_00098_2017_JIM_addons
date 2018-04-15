# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np


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
        # least-squares solution to a linear matrix equation.
        x = np.array([0, 1, 2, 3, 4])
        y = np.array([product_id.year5_ago,
                      product_id.year4_ago,
                      product_id.year3_ago,
                      product_id.year2_ago,
                      product_id.year1_ago])
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y)[0]
        demand = m * 5 + c
        if demand < 0:
            demand = 0
        return demand

    @api.model
    def _get_sales(self, product_id):
        #company_id = self.env.user.company_id.id
        query = """
                    SELECT  Sum(
                    case WHEN product_uom_qty - qty_delivered >= 0
                      THEN product_uom_qty - qty_delivered
                      ELSE 0 END) 
                     FROM sale_order_line WHERE
                      product_id = %s 
                      and state in ('lqdr','pending', 'progress',
                       'progress_lqdr','sale')
                    GROUP BY product_id
                """ % (product_id)

        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            return qty
        return 0

    @api.multi
    def _get_qty_year_ago(self, product_id, num_years_ago=0):
        self.ensure_one()
        qty = 0
        today = datetime.today()
        future_date = today + relativedelta(months=+self.stock_months)

        year_today = today.year - num_years_ago
        year_future = future_date.year - num_years_ago
        month_today = today.strftime("%m")
        month_future = future_date.strftime("%m")

        day_today = today.strftime("%d")
        day_future = future_date.strftime("%d")

        date_start = str(year_today) + '-' + month_today + '-' + day_today
        date_end = str(year_future) + '-' + month_future + '-' + day_future
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
            return qty
        return 0




    @api.multi
    def create_lines(self):
        self.ensure_one()
        self.delete_forecast_lines()
        products = self.env['product.product'].\
            search([('categ_id', '=', self.category_id.id)])
        for product in products:
            ventas = self._get_sales(product.id)
            vals = {
                'forecast_id': self.id,
                'product_id': product.id,
                'year1_ago': self._get_qty_year_ago(product.id, 1),
                'year2_ago': self._get_qty_year_ago(product.id, 2),
                'year3_ago': self._get_qty_year_ago(product.id, 3),
                'year4_ago': self._get_qty_year_ago(product.id, 4),
                'year5_ago': self._get_qty_year_ago(product.id, 5),
                'sales': ventas,
                'stock': product.global_real_stock
            }
            line = self.env['purchase.forecast.line'].create(vals)
            line.demand = self._get_demand(line)
            purchase = max(line.demand, ventas) - product.global_real_stock
            line.seller_id = product.seller_ids and product.seller_ids[0] \
                             and product.seller_ids[0].name or False
            line.harbor_id = line.seller_id and line.seller_id.harbor_ids and\
                            line.seller_id.harbor_ids[0] or False

            if purchase < 0:
                purchase = 0
            line.purchase = purchase

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
    sales = fields.Float('Confirmed Sales')
    purchase = fields.Float('Recommended purchase')
    stock = fields.Float('Current Stock')
    seller_id = fields.Many2one('res.partner', 'Seller')
    harbor_id = fields.Many2one('res.harbor', 'Harbor')
