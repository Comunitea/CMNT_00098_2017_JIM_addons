# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from odoo.tools import float_is_zero

class ProductProduct(models.Model):

    _inherit = "product.product"

    demand = fields.Float('Demand', readonly=True)
    purchase = fields.Float('Recommended purchase', readonly=True)

    @api.multi
    def _get_qty_current_year(self):
        self.ensure_one()
        qty = 0
        today = datetime.today()

        year_today = today.year
        date_end = today.strftime("%d-%m-%y")
        date_start = str(year_today) + '-01-01'
        company_id = self.env.user.company_id.id

        # Query odoo sales from outgoings moves
        qty2 = 0
        query2 = """
                SELECT sum(product_uom_qty)
                FROM stock_move sm
                INNER JOIN stock_picking sp on sp.id = sm.picking_id
                INNER JOIN stock_picking_type spt on spt.id = sp.picking_type_id
                INNER JOIN stock_location sl on sl.id = sp.location_dest_id
                WHERE sm.product_id = %s  AND
                      sm.date_expected >= '%s' AND sm.date_expected <= '%s' AND
                      sp.state in ('done') AND
                      spt.code = 'outgoing' AND sl.usage = 'customer' AND
                      sp.partner_id not in (select partner_id from res_company)
            """ % (self.id, date_start, date_end)
        self._cr.execute(query2)
        qres = self._cr.fetchall()
        if qres:
            qty2 = qres[0][0]
            if not qty2:
                qty2 = 0
        return qty2

    @api.multi
    def _get_sales(self):
        self.ensure_one()
        # query = """
        #     SELECT  Sum(
        #     case WHEN product_uom_qty - qty_delivered >= 0
        #       THEN product_uom_qty - qty_delivered
        #       ELSE 0 END)
        #      FROM sale_order_line WHERE
        #       product_id = %s
        #       and state in ('lqdr','pending', 'progress',
        #        'progress_lqdr','sale')
        #     GROUP BY product_id
        # """ % (self.id)
        #
        # self._cr.execute(query)
        # qres = self._cr.fetchall()
        # if qres:
        #     qty = qres[0][0]
        #     return qty
        # return 0
        return self.global_real_stock - self.web_global_stock

    @api.multi
    def get_dates(self, num_years_ago=0, stock_months=4):
        def check(day, month):
            if day == '31' and month in ['04', '06', '09', '11']:
                return '30'
            if month == '02' and day in ['29', '30', '31']:
                return '28'
            return day
        self.ensure_one()
        today = datetime.today()
        future_date = today + relativedelta(months=+stock_months)

        year_today = today.year - num_years_ago
        year_future = future_date.year - num_years_ago
        month_today = today.strftime("%m")
        month_future = future_date.strftime("%m")
        day_today = today.strftime("%d")
        day_future = future_date.strftime("%d")

        day_today = check(day_today, month_today)
        day_future = check(day_future, month_future)

        date_start = str(year_today) + '-' + month_today + '-' + day_today
        date_end = str(year_future) + '-' + month_future + '-' + day_future
        return date_start, date_end

    @api.multi
    def _get_qty_year_ago(self, num_years_ago=0, stock_months=4):
        self.ensure_one()
        qty = 0
        date_start, date_end = self.get_dates(num_years_ago, stock_months)
        company_id = self.env.user.company_id.id

        # Query sale hystory
        query = """
            SELECT sum(qty)
            FROM sale_history
            WHERE date >= '%s' AND
                  date <= '%s' AND product_id = %s AND company_id = %s
            GROUP BY product_id
        """ % (date_start, date_end, self.id, company_id)

        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            if not qty:
                qty = 0

        # Query odoo sales from outgoings moves
        qty2 = 0
        query2 = """
            SELECT sum(product_uom_qty)
            FROM stock_move sm
            INNER JOIN stock_picking sp on sp.id = sm.picking_id
            INNER JOIN stock_picking_type spt on spt.id = sp.picking_type_id
            INNER JOIN stock_location sl on sl.id = sp.location_dest_id
            WHERE sm.product_id = %s  AND
                  sm.date_expected >= '%s' AND sm.date_expected <= '%s' AND
                  sp.state in ('done') AND
                  spt.code = 'outgoing' AND sl.usage = 'customer' AND
                  sp.partner_id not in (select partner_id from res_company)
        """ % (self.id, date_start, date_end)
        self._cr.execute(query2)
        qres = self._cr.fetchall()
        if qres:
            qty2 = qres[0][0]
            if not qty2:
                qty2 = 0
        return qty + qty2

    @api.multi
    def _get_incoming_stock_months(self, stock_months=4):
        """
        Get purchase qty in stock motns range
        """
        qty = 0
        self.ensure_one()
        date_start, date_end = self.get_dates(stock_months=stock_months)
        query = """
            SELECT sum(product_uom_qty)
            FROM stock_move sm
            INNER JOIN stock_picking sp on sp.id = sm.picking_id
            INNER JOIN stock_picking_type spt on spt.id = sp.picking_type_id
            INNER JOIN stock_location sl on sl.id = sp.location_id
            WHERE sm.product_id = %s  AND
                  sm.date_expected >= '%s' AND sm.date_expected <= '%s' AND
                  sp.state in ('assigned', 'partially_available') AND
                  spt.code = 'incoming' AND sl.usage = 'supplier' AND
                  sp.partner_id not in (select partner_id from res_company)
        """ % (self.id, date_start, date_end)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            if not qty:
                qty = 0
        return qty

    @api.multi
    def _get_incoming_remaining(self, stock_months=4):
        """
        Get purchase out of stock moths range
        """
        qty = 0
        self.ensure_one()
        date_start, date_end = self.get_dates(stock_months=stock_months)
        query = """
            SELECT sum(product_uom_qty)
            FROM stock_move sm
            INNER JOIN stock_picking sp on sp.id = sm.picking_id
            INNER JOIN stock_picking_type spt on spt.id = sp.picking_type_id
            INNER JOIN stock_location sl on sl.id = sp.location_id
            WHERE sm.product_id = %s  AND
                  sm.date_expected < '%s' AND sm.date_expected > '%s' AND
                  sp.state in ('assigned', 'partially_available') AND
                  spt.code = 'incoming' AND sl.usage = 'supplier' AND
                  sp.partner_id not in (select partner_id from res_company)
        """ % (self.id, date_start, date_end)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            if not qty:
                qty = 0
        return qty

    @api.multi
    def _get_pending_purchase(self):
        """
        Get purchase out of stock moths range
        """
        self.ensure_one()
        qty = 0
        query = """
            SELECT sum(product_qty)
            FROM purchase_order_line pol
            INNER JOIN purchase_order po on po.id = pol.order_id
            WHERE pol.product_id = %s  AND
                  po.state not in ('cancel', 'purchase', 'done')
        """ % (self.id)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            if not qty:
                qty = 0
        return qty

    @api.multi
    def _get_related_purchase_id(self):
        """
        Get purchase out of stock moths range
        """
        self.ensure_one()
        po_id = False
        query = """
            SELECT min(po.id)
            FROM purchase_order_line pol
            INNER JOIN purchase_order po on po.id = pol.order_id
            WHERE pol.product_id = %s  AND
                  po.state not in ('cancel', 'purchase', 'done')
        """ % (self.id)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            po_id = qres[0][0]
            if not po_id:
                po_id = False
        return po_id

    @api.multi
    def _get_related_picking_id(self):
        """
        Get purchase out of stock moths range
        """
        self.ensure_one()
        picking_id = False
        query = """
            SELECT min(sp.id)
            FROM stock_move sm
            INNER JOIN stock_picking sp on sp.id = sm.picking_id
            INNER JOIN stock_picking_type spt on spt.id = sp.picking_type_id
            INNER JOIN stock_location sl on sl.id = sp.location_id
            WHERE sm.product_id = %s  AND
                  sp.state in ('assigned', 'partially_available') AND
                  spt.code = 'incoming' AND sl.usage = 'supplier' AND
                  sp.partner_id not in (select partner_id from res_company)
        """ % (self.id)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            pick_id = qres[0][0]
            if pick_id:
                picking_id = pick_id
        return picking_id

    @api.multi
    def _get_forecast_line_vals(self, stock_months=4):
        self.ensure_one()
        ventas = self._get_sales()
        current_year_sales = self._get_qty_current_year()
        vals = {
            'product_id': self.id,
            'year1_ago': self._get_qty_year_ago(1, stock_months),
            'year2_ago': self._get_qty_year_ago(2, stock_months),
            'year3_ago': self._get_qty_year_ago(3, stock_months),
            'year4_ago': self._get_qty_year_ago(4, stock_months),
            'year5_ago': self._get_qty_year_ago(5, stock_months),
            'sales': ventas,
            'current_year_sales': current_year_sales,
            'incoming_months': self._get_incoming_stock_months(stock_months),
            'incoming_remaining': self._get_incoming_remaining(stock_months),
            'pending_purchase': self._get_pending_purchase(),
            'related_purchase_id':
            self._get_related_purchase_id(),
            'related_picking_id':
            self._get_related_picking_id(),
            'stock': self.global_real_stock
        }
        return vals

    @api.multi
    def _get_demand(self, line_vals):
        # least-squares solution to a linear matrix equation.
        #if not float_is_zero(line_vals['year5_ago'], precision_digits=2) :
        #    n = 5
        #elif not float_is_zero(line_vals['year4_ago'], precision_digits=2):
        if not float_is_zero(line_vals['year4_ago'], precision_digits=2):
            n = 4
        elif not float_is_zero(line_vals['year3_ago'], precision_digits=2):
            n = 3
        elif not float_is_zero(line_vals['year2_ago'], precision_digits=2):
            n = 2
        elif not float_is_zero(line_vals['year1_ago'], precision_digits=2):
            n = 1
        else:
            n = 0

        if n == 0:
            demand = 0
        elif n == 1:
            demand = line_vals['year1_ago']
        else:
            x = np.arange(n)
            years = []
            for i in range(0, n):
                years.append(line_vals['year'+str(n-i)+'_ago'])
        # y = np.array([line_vals['year5_ago'],
        #           line_vals['year4_ago'],
        #           line_vals['year3_ago'],
        #           line_vals['year2_ago'],
        #           line_vals['year1_ago']])
            y = np.array(years)
            a = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(a, y)[0]
            demand = m * n + c
        if demand < 0:
            demand = 0
        return demand

    @api.multi
    def _get_purchase(self, demand, line_vals):
        ventas = line_vals['sales']
        incoming_months = line_vals['incoming_months']
        purchase = max(demand, ventas) - self.global_real_stock - \
            incoming_months
        return purchase if purchase>0 else 0

    @api.multi
    def get_all_forecast(self):
        self.search([('type','=','product')]).get_purchase_forecast()


    @api.multi
    def get_purchase_forecast(self):
        for product in self:
            line_vals = product._get_forecast_line_vals()
            demand = product._get_demand(line_vals)
            purchase = product._get_purchase(demand, line_vals)
            product.write({'demand': demand,
                           'purchase': purchase})
