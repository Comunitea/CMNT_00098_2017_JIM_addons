# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def _get_customer_prices_count(self):
        for tmpl in self:
            tmpl.customer_prices_count = len(tmpl.customer_tmpl_prices)

    lqdr = fields.Boolean('LQDR')
    customer_tmpl_prices = fields.One2many('customer.price', 'product_tmpl_id',
                                           'Customer Prices')
    customer_prices_count = fields.\
        Integer(compute='_get_customer_prices_count', string='#Prices')


class ProductPricelist(models.Model):

    _inherit = "product.pricelist"

    legacy_code = fields.Char(size=5)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def _sales_count(self):
        r = {}
        domain = [
            ('state', 'in', ['sale', 'done', 'proforma', 'lqdr',
                             'progress_lqdr', 'pending', 'progress']),
            ('product_id', 'in', self.ids),
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id',
                                                                 'product_uom_qty'],
                                                        ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            product.sales_count = r.get(product.id, 0)
        return r


    @api.multi
    def _get_customer_prices_count(self):
        for prod in self:
            prod.customer_prices_count = len(prod.customer_product_prices)

    customer_product_prices = fields.One2many('customer.price', 'product_id',
                                              'Customer Prices')
    customer_prices_count = fields.\
        Integer(compute='_get_customer_prices_count', string='#Prices')

    def get_price_from_web(self, partner_id, quantity=1):
        ctx = dict(self.env.context)
        pricelist_id = self.env['res.partner'].browse(
            partner_id).property_product_pricelist
        ctx.update({
            'partner': partner_id,
            'pricelist': pricelist_id.id,
            'quantity': quantity
        })
        return self.with_context(ctx).price

    def _compute_product_price(self):
        """
        When read price, search in customer prices first
        """
        self_super = self.env['product.product']
        partner_id = self._context.get('partner', False)
        qty = self._context.get('quantity', 1.0)
        if partner_id:
            for product in self:
                customer_price = self.env['customer.price'].\
                    get_customer_price(partner_id, product, qty)
                if customer_price:
                    product.price = customer_price
                else:
                    self_super += product
        return super(ProductProduct, self_super)._compute_product_price()
