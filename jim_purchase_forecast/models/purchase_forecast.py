# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, exceptions, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np


class PurchaseForecast(models.Model):

    _name = "purchase.forecast"

    name = fields.Char('Name', required=True)
    category_ids = fields.Many2many('product.category',
                                    string='Product Categorys',
                                    required=False)
    lines_count = fields.Float('Nº Lines', compute='_get_lines_count')
    stock_months = fields.Integer('Stock Months')
    seller_id = fields.Many2one('res.partner', 'Seller',
                                domain=[('supplier', '=', True)])
    harbor_id = fields.Many2one('res.harbor', 'Harbor')

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
        a = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(a, y)[0]
        demand = m * 5 + c
        if demand < 0:
            demand = 0
        return demand

    @api.model
    def _get_sales(self, product_id):
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
    def get_dates(self, num_years_ago=0):
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
        return date_start, date_end

    @api.multi
    def _get_qty_year_ago(self, product_id, num_years_ago=0):
        self.ensure_one()
        qty = 0
        date_start, date_end = self.get_dates(num_years_ago)
        print date_start
        print date_end
        company_id = self.env.user.company_id.id

        # Query sale hystory
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
        """ % (product_id, date_start, date_end)
        self._cr.execute(query2)
        qres = self._cr.fetchall()
        if qres:
            qty2 = qres[0][0]
            if not qty2:
                qty2 = 0
        return qty + qty2

    @api.multi
    def _query_product_category(self):
        res = ("", {})
        if self.category_ids:
            query = """
                SELECT pp.id
                FROM product_product pp
                INNER JOIN product_template pt on pt.id = pp.product_tmpl_id
                WHERE pt.categ_id in %(categ_ids)s
            """
            params = {
                'categ_ids': tuple(self.category_ids.ids)
            }
            res = (query, params)
        return res

    @api.multi
    def _query_product_seller(self):
        res = ("", {})
        if self.seller_id:
            query = """
                SELECT pp.id
                FROM product_product pp
                INNER JOIN product_template pt
                    on pt.id = pp.product_tmpl_id
                INNER JOIN product_supplierinfo psi
                    on psi.product_tmpl_id = pt.id
                WHERE psi.name = %(seller_id)s
            """
            params = {'seller_id': self.seller_id.id}
            res = (query, params)
        return res

    @api.multi
    def _query_product_harbor(self):
        res = ("", {})
        if self.harbor_id:
            query = """
                SELECT pp.id
                FROM product_product pp
                INNER JOIN product_template pt on pt.id = pp.product_tmpl_id
                INNER JOIN product_supplierinfo psi
                    on psi.product_tmpl_id = pt.id
                INNER JOIN res_partner rp on rp.id = psi.name
                INNER JOIN res_harbor_res_partner_rel rhp
                    on rhp.res_partner_id = rp.id
                WHERE  rhp.res_harbor_id = %(harbor_id)s
            """
            params = {'harbor_id': self.harbor_id.id}
            res = (query, params)
        return res

    @api.multi
    def _get_products(self):
        self.ensure_one()
        # One query by filter
        query_category, map1 = self._query_product_category()
        query_seller, map2 = self._query_product_seller()
        query_harbor, map3 = self._query_product_harbor()

        # Mmaking union of existing queries if exist
        intersect_separator = "\nINTERSECT\n"
        product_query = ""
        if query_category:
            product_query += query_category
        if query_seller:
            separator = ''
            if product_query:
                separator = intersect_separator
            product_query += separator + query_seller
        if query_harbor:
            separator = ''
            if product_query:
                separator = intersect_separator
            product_query += separator + query_harbor

        if not product_query:
            raise exceptions.UserError(_('You need to select one filter \
                                          condition.'))
        # Query products search execution
        map_dic = {}
        map_dic.update(map1)
        map_dic.update(map2)
        map_dic.update(map3)
        self._cr.execute(product_query, map_dic)
        qres = self._cr.fetchall()

        product_ids = [t[0] for t in qres]
        if not product_ids:
            raise exceptions.UserError(_('No products founded. No forecast \
                                          lines created'))
        return self.env['product.product'].browse(product_ids)

    def _get_incoming_stock_months(self, product_id):
        """
        Get purchase qty in stock motns range
        """
        date_start, date_end = self.get_dates()
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
        """ % (product_id, date_start, date_end)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            return qty
        return 0

    def _get_incoming_remaining(self, product_id):
        """
        Get purchase out of stock moths range
        """
        date_start, date_end = self.get_dates()
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
        """ % (product_id, date_start, date_end)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            return qty
        return 0

    def _get_pending_purchase(self, product_id):
        """
        Get purchase out of stock moths range
        """
        qty = 0
        query = """
            SELECT sum(product_qty)
            FROM purchase_order_line pol
            INNER JOIN purchase_order po on po.id = pol.order_id
            WHERE pol.product_id = %s  AND
                  po.state not in ('cancel', 'purchase', 'done')
        """ % (product_id)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            qty = qres[0][0]
            if not qty:
                qty = 0
        return qty

    def _get_related_purchase_id(self, product_id):
        """
        Get purchase out of stock moths range
        """
        po_id = False
        query = """
            SELECT min(po.id)
            FROM purchase_order_line pol
            INNER JOIN purchase_order po on po.id = pol.order_id
            WHERE pol.product_id = %s  AND
                  po.state not in ('cancel', 'purchase', 'done')
        """ % (product_id)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            po_id = qres[0][0]
            if not po_id:
                po_id = False
        return po_id

    def _get_related_picking_id(self, product_id):
        """
        Get purchase out of stock moths range
        """
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
        """ % (product_id)
        self._cr.execute(query)
        qres = self._cr.fetchall()
        if qres:
            pick_id = qres[0][0]
            if pick_id:
                picking_id = pick_id
        return picking_id

    @api.multi
    def create_lines(self):
        self.ensure_one()
        self.delete_forecast_lines()
        products = self._get_products()
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
                'incoming_months': self._get_incoming_stock_months(product.id),
                'incoming_remaining': self._get_incoming_remaining(product.id),
                'pending_purchase': self._get_pending_purchase(product.id),
                'related_purchase_id':
                self._get_related_purchase_id(product.id),
                'related_picking_id':
                self._get_related_picking_id(product.id),
                'stock': product.global_real_stock
            }
            line = self.env['purchase.forecast.line'].create(vals)
            line.demand = self._get_demand(line)
            purchase = max(line.demand, ventas) - product.global_real_stock \
                - line.incoming_months
            line.seller_id = product.seller_ids and product.seller_ids[0] \
                and product.seller_ids[0].name or False
            line.seller_price = line.seller_id and product.seller_ids[0].price
            line.seller2_id = product.seller_ids and len(product.seller_ids)\
                              > 1 and product.seller_ids[1] \
                             and product.seller_ids[1].name or False
            line.seller2_price = line.seller2_id and product.seller_ids[
                1].price
            line.harbor_id = line.seller_id and line.seller_id.harbor_ids and\
                line.seller_id.harbor_ids[0] or False
            line.harbor2_id = line.seller2_id and line.seller2_id.harbor_ids \
                              and line.seller2_id.harbor_ids[0] or False

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
    incoming_months = fields.Float('Incoming Pending (Stock Months)')
    incoming_remaining = fields.Float('Incoming Pending (Remaining)')
    related_picking_id = fields.Many2one('stock.picking', 'Related Pickig')
    pending_purchase = fields.Float('Pending Purchases')
    related_purchase_id = fields.Many2one('purchase.order',
                                          'Related Purchase')
    seller_id = fields.Many2one('res.partner', 'Seller')
    seller2_id = fields.Many2one('res.partner', 'Seller 2')
    seller_price = fields.Float('Price 1')
    seller2_price = fields.Float('Price 2')
    harbor_id = fields.Many2one('res.harbor', 'Harbor')
    harbor2_id = fields.Many2one('res.harbor', 'Harbor 2')
