# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, exceptions, _
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
    tag_ids = fields. Many2many('product.tag', string='Product Tags')
    date = fields.Date('Calculation Date', readonly=True)

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
        x = np.array([0, 1, 2, 3])
        y = np.array([product_id.year4_ago,
                      product_id.year3_ago,
                      product_id.year2_ago,
                      product_id.year1_ago])
        a = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(a, y)[0]
        demand = m * 4 + c
        if demand < 0:
            demand = 0
        return demand

    @api.multi
    def _query_product_tags(self):
        res = ("", {})
        if self.tag_ids:
            # Los campos tag_id y product_id de la tabla de relación tienen
            # los nombres cambiados
            query = """
                    SELECT pp.id
                    FROM product_product pp
                    INNER JOIN product_product_tag_rel pptl ON 
                    pptl.tag_id = pp.product_tmpl_id
                    WHERE pptl.product_id in %(tag_ids)s
                """
            params = {
                'tag_ids': tuple(self.tag_ids.ids)
            }
            res = (query, params)
        return res

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
                SELECT DISTINCT(pp.id)
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
                SELECT DISTINCT(pp.id)
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
        query_tags, map4 = self._query_product_tags()

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
        if query_tags:
            separator = ''
            if product_query:
                separator = intersect_separator
            product_query += separator + query_tags

        if not product_query:
            raise exceptions.UserError(_('You need to select one filter \
                                          condition.'))
        # Query products search execution
        map_dic = {}
        map_dic.update(map1)
        map_dic.update(map2)
        map_dic.update(map3)
        map_dic.update(map4)
        self._cr.execute(product_query, map_dic)
        qres = self._cr.fetchall()

        product_ids = [t[0] for t in qres]
        if not product_ids:
            raise exceptions.UserError(_('No products founded. No forecast \
                                          lines created'))
        product_ids = list(set(product_ids))
        return self.env['product.product'].browse(product_ids)

    @api.multi
    def create_lines(self):
        self.ensure_one()
        self.delete_forecast_lines()
        self.date = fields.Date.today()
        products = self._get_products()
        seller_id = False

        for product in products:
            line_vals = product._get_forecast_line_vals(self.stock_months)
            line_vals['forecast_id'] = self.id

            # REFACTORIZADO
            line_demand = product._get_demand(line_vals)
            line_purchase = product._get_purchase(line_demand, line_vals)
            if self.seller_id:
                seller = self.seller_id
                seller_line = product.seller_ids.filtered(lambda x:
                                                          x.name == seller)
                seller_line = seller_line and seller_line[0] or False
            else:
                seller_line = product.seller_ids and product.seller_ids[0] \
                              and product.seller_ids[0] or False
                seller = seller_line and seller_line.name or False
            seller_price = seller_line and seller_line.price or False
            harbor = seller_line and seller_line.name.harbor_ids and \
                     seller_line.name.harbor_ids[0] and \
                     seller_line.name.harbor_ids[0].id or False

            seller2_line = product.seller_ids.filtered(lambda x:
                                                       x.name != seller)
            seller2_line = seller2_line and seller2_line[0] or False
            seller2_id = seller2_line and seller2_line.name and \
                         seller2_line.name.id or False
            seller2_price = seller2_line and seller2_line.price or False
            harbor2 = seller2_line and seller2_line.name.harbor_ids and \
                      seller2_line.name.harbor_ids[0] and \
                      seller2_line.name.harbor_ids[0].id or False

            line_vals2 = {
                'demand': line_demand,
                'purchase': line_purchase if line_purchase > 0 else 0,
                'seller_id': seller and seller.id or False,
                'seller_price': seller_price,
                'seller2_id': seller2_id,
                'seller2_price': seller2_price,
                'harbor_id': harbor,
                'harbor2_id': harbor2
            }

            line_vals.update(line_vals2)
            self.env['purchase.forecast.line'].create(line_vals)
        return

    @api.multi
    def show_lines(self):
        self.ensure_one()
        action = self.env.ref('jim_purchase_forecast.action_forecast_lines').\
            read()[0]
        action['domain'] = [('forecast_id', '=', self.id)]
        return action


class PurchaseForecastLine(models.Model):

    _name = "purchase.forecast.line"

    forecast_id = fields.Many2one('purchase.forecast', 'Forecast',
                                  readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    year1_ago = fields.Float('1 Year Ago', readonly=True)
    year2_ago = fields.Float('2 Year Ago', readonly=True)
    year3_ago = fields.Float('3 Year Ago', readonly=True)
    year4_ago = fields.Float('4 Year Ago', readonly=True)
    year5_ago = fields.Float('5 Year Ago', readonly=True)
    demand = fields.Float('Demand', readonly=True)
    sales = fields.Float('Pending Sales', readonly=True)
    current_year_sales = fields.Float('Current Year Sales', readonly=True)
    purchase = fields.Float('Recommended purchase', readonly=True)
    to_buy = fields.Float('To Buy')
    stock = fields.Float('Current Stock', readonly=True)
    incoming_months = fields.Float('Incoming Pending (Stock Months)', readonly=True)
    incoming_remaining = fields.Float('Incoming Pending (Remaining)', readonly=True)
    related_picking_id = fields.Many2one('stock.picking', 'Related Pickig', readonly=True)
    pending_purchase = fields.Float('Pending Purchases', readonly=True)
    related_purchase_id = fields.Many2one('purchase.order', 'Related '
                                                            'Purchase',
                                          readonly=True)
    seller_id = fields.Many2one('res.partner', 'Seller',readonly=True)
    seller2_id = fields.Many2one('res.partner', 'Seller 2',readonly=True)
    seller_price = fields.Float('Price 1',readonly=True)
    seller2_price = fields.Float('Price 2',readonly=True)
    harbor_id = fields.Many2one('res.harbor', 'Harbor',readonly=True)
    harbor2_id = fields.Many2one('res.harbor', 'Harbor 2',readonly=True)

    @api.multi
    def open_form_view(self):
        self.ensure_one()
        action_name = 'jim_purchase_forecast.action_forecast_lines'
        view_name = 'jim_purchase_forecast.purchase_forecast_line_view_form'
        view = self.env.ref(view_name)
        action = self.env.ref(action_name)
        action = action.read()[0]
        action['views'] = [(view.id, u'form')]
        action['res_id'] = self.ids[0]
        return action
